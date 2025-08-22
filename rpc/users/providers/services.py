from fastapi import HTTPException, Request
from pydantic import ValidationError
import uuid

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
  await db.run(rpc_request.op, {
    "guid": auth_ctx.user_guid,
    "provider": payload.provider,
  })
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
    try:
      client_secret = await db.get_google_api_secret()
    except ValueError:
      raise HTTPException(status_code=500, detail="Google OAuth client_secret not configured")
    res_redirect = await db.run("urn:system:config:get_config:1", {"key": "GoogleAuthRedirectLocalhost"})
    if not res_redirect.rows:
      raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
    redirect_uri = res_redirect.rows[0]["value"]
    id_token, access_token = await exchange_code_for_tokens(
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
  await db.run(
    "urn:users:providers:unlink_provider:1",
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

