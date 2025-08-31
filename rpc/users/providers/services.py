from fastapi import HTTPException, Request
from pydantic import ValidationError
import uuid
from datetime import datetime, timezone

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from .models import (
  UsersProvidersSetProvider1,
  UsersProvidersLinkProvider1,
  UsersProvidersUnlinkProvider1,
  UsersProvidersGetByProviderIdentifier1,
  UsersProvidersCreateFromProvider1,
)
from rpc.auth.google.services import exchange_code_for_tokens
from rpc.auth.microsoft.services import exchange_code_for_tokens as ms_exchange_code_for_tokens


def normalize_provider_identifier(pid: str) -> str:
  try:
    return str(uuid.UUID(pid))
  except ValueError:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, pid))

async def users_providers_set_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersSetProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  auth: AuthModule | None = getattr(request.app.state, "auth", None)
  await db.run(rpc_request.op, {
    "guid": auth_ctx.user_guid,
    "provider": payload.provider,
  })
  if auth:
    provider = getattr(auth, "providers", {}).get(payload.provider)
    if provider:
      try:
        profile = await provider.fetch_user_profile(None)
        await db.run(
          "urn:users:profile:update_if_unedited:1",
          {
            "guid": auth_ctx.user_guid,
            "email": profile.get("email"),
            "display_name": profile.get("username"),
          },
        )
      except Exception:
        pass
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_providers_link_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersLinkProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db
  if payload.provider == "google":
    google_provider = getattr(auth, "providers", {}).get("google")
    if not google_provider or not google_provider.audience:
      raise HTTPException(status_code=500, detail="Google OAuth client_id not configured")
    client_id = google_provider.audience
    env = request.app.state.env
    client_secret = env.get("GOOGLE_AUTH_SECRET")
    if not client_secret:
      raise HTTPException(status_code=500, detail="Google OAuth client_secret not configured")
    res_redirect = await db.run("urn:system:config:get_config:1", {"key": "Hostname"})
    if not res_redirect.rows:
      raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
    redirect_uri = res_redirect.rows[0]["value"]
    id_token, access_token = await exchange_code_for_tokens(
      payload.code,
      client_id,
      client_secret,
      redirect_uri,
    )
  elif payload.provider == "microsoft":
    ms_provider = getattr(auth, "providers", {}).get("microsoft")
    if not ms_provider or not ms_provider.audience:
      raise HTTPException(status_code=500, detail="Microsoft OAuth client_id not configured")
    client_id = ms_provider.audience
    env = request.app.state.env
    client_secret = env.get("MICROSOFT_AUTH_SECRET")
    if not client_secret:
      raise HTTPException(status_code=500, detail="Microsoft OAuth client_secret not configured")
    res_redirect = await db.run("urn:system:config:get_config:1", {"key": "Hostname"})
    if not res_redirect.rows:
      raise HTTPException(status_code=500, detail="Microsoft OAuth redirect URI not configured")
    redirect_uri = res_redirect.rows[0]["value"]
    id_token, access_token = await ms_exchange_code_for_tokens(
      payload.code,
      client_id,
      client_secret,
      redirect_uri,
    )
  else:
    raise HTTPException(status_code=400, detail="Unsupported auth provider")
  provider_uid, _, _ = await auth.handle_auth_login(payload.provider, id_token, access_token)
  provider_uid = normalize_provider_identifier(provider_uid)
  res = await db.run(
    "urn:users:providers:get_by_provider_identifier:1",
    {"provider": payload.provider, "provider_identifier": provider_uid},
  )
  if res.rows and res.rows[0].get("guid") != auth_ctx.user_guid:
    raise HTTPException(status_code=409, detail="Provider already linked")
  await db.run(
    "urn:users:providers:link_provider:1",
    {
      "guid": auth_ctx.user_guid,
      "provider": payload.provider,
      "provider_identifier": provider_uid,
    },
  )
  return RPCResponse(op=rpc_request.op, payload={"provider": payload.provider}, version=rpc_request.version)

async def users_providers_unlink_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersUnlinkProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  res_prof = await db.run(
    "urn:users:profile:get_profile:1",
    {"guid": auth_ctx.user_guid},
  )
  default_provider = res_prof.rows[0].get("default_provider") if res_prof.rows else None
  res = await db.run(
    "urn:users:providers:unlink_provider:1",
    {"guid": auth_ctx.user_guid, "provider": payload.provider},
  )
  remaining = res.rows[0].get("providers_remaining") if res.rows else 0
  if remaining == 0:
    await db.run(
      "urn:users:providers:soft_delete_account:1",
      {"guid": auth_ctx.user_guid},
    )
    await db.run(
      "db:auth:session:revoke_all_device_tokens:1",
      {"guid": auth_ctx.user_guid},
    )
    now = datetime.now(timezone.utc)
    await db.run(
      "db:users:session:set_rotkey:1",
      {"guid": auth_ctx.user_guid, "rotkey": "", "iat": now, "exp": now},
    )
  elif payload.provider == default_provider:
    if not payload.new_default:
      raise HTTPException(status_code=400, detail="new_default required")
    await db.run(
      "urn:users:providers:set_provider:1",
      {"guid": auth_ctx.user_guid, "provider": payload.new_default},
    )
    await db.run(
      "db:auth:session:revoke_provider_tokens:1",
      {"guid": auth_ctx.user_guid, "provider": payload.provider},
    )
  return RPCResponse(op=rpc_request.op, payload={"provider": payload.provider}, version=rpc_request.version)

async def users_providers_get_by_provider_identifier_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersGetByProviderIdentifier1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  res = await db.run(
    "urn:users:providers:get_by_provider_identifier:1",
    payload.model_dump(),
  )
  row = res.rows[0] if res.rows else None
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)

async def users_providers_create_from_provider_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersCreateFromProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  res = await db.run(
    "urn:users:providers:get_user_by_email:1",
    {"email": payload.provider_email},
  )
  if res.rows:
    raise HTTPException(status_code=409, detail="Email already registered")
  res = await db.run(
    "urn:users:providers:create_from_provider:1",
    payload.model_dump(),
  )
  row = res.rows[0] if res.rows else None
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)

