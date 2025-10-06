from fastapi import HTTPException, Request
from pydantic import ValidationError
import uuid

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from .models import (
  UsersProvidersSetProvider1,
  UsersProvidersLinkProvider1,
  UsersProvidersUnlinkProvider1,
  UsersProvidersGetByProviderIdentifier1,
  UsersProvidersCreateFromProvider1,
)
from server.modules.oauth_module import OauthModule
from server.registry.content.profile import (
  get_profile_request,
  update_if_unedited_request,
)
from server.registry.users.security.identities import (
  create_from_provider_request,
  get_by_provider_identifier_request,
  get_user_by_email_request,
  link_provider_request,
  set_provider_request,
  unlink_last_provider_request,
  unlink_provider_request,
)
from server.registry.users.security.sessions import revoke_provider_tokens_request
from server.registry.system.config import get_config_request


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
  auth: AuthModule = request.app.state.auth
  oauth: OauthModule = request.app.state.oauth
  profile = None
  if payload.code or (payload.id_token and payload.access_token):
    if payload.provider == "google":
      if payload.code:
        google_provider = getattr(auth, "providers", {}).get("google")
        if not google_provider or not google_provider.audience:
          raise HTTPException(status_code=500, detail="Google OAuth client_id not configured")
        client_id = google_provider.audience
        env = request.app.state.env
        client_secret = env.get("GOOGLE_AUTH_SECRET")
        if not client_secret:
          raise HTTPException(status_code=500, detail="Google OAuth client_secret not configured")
        res_redirect = await db.run(get_config_request("Hostname"))
        if not res_redirect.rows:
          raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
        redirect_uri = res_redirect.rows[0]["value"]
        id_token, access_token = await oauth.exchange_code_for_tokens(
          payload.code,
          client_id,
          client_secret,
          redirect_uri,
          payload.provider,
        )
        if not id_token:
          raise HTTPException(status_code=400, detail="Missing id_token")
      else:
        id_token, access_token = payload.id_token, payload.access_token
    elif payload.provider == "discord":
      discord_provider = getattr(auth, "providers", {}).get("discord")
      if not discord_provider or not getattr(discord_provider, "audience", None):
        raise HTTPException(status_code=500, detail="Discord OAuth client_id not configured")
      if payload.code:
        client_id = getattr(discord_provider, "audience")
        env = request.app.state.env
        client_secret = env.get("DISCORD_AUTH_SECRET")
        if not client_secret:
          raise HTTPException(status_code=500, detail="Discord OAuth client_secret not configured")
        res_redirect = await db.run(get_config_request("Hostname"))
        if not res_redirect.rows:
          raise HTTPException(status_code=500, detail="Discord OAuth redirect URI not configured")
        redirect_uri = res_redirect.rows[0]["value"]
        id_token, access_token = await oauth.exchange_code_for_tokens(
          payload.code,
          client_id,
          client_secret,
          redirect_uri,
          payload.provider,
        )
      else:
        if not payload.access_token:
          raise HTTPException(status_code=400, detail="access_token required")
        id_token, access_token = payload.id_token, payload.access_token
    elif payload.provider == "microsoft":
      ms_provider = getattr(auth, "providers", {}).get("microsoft")
      if not ms_provider or not ms_provider.audience:
        raise HTTPException(status_code=500, detail="Microsoft OAuth client_id not configured")
      if payload.code:
        client_id = ms_provider.audience
        env = request.app.state.env
        client_secret = env.get("MICROSOFT_AUTH_SECRET")
        if not client_secret:
          raise HTTPException(status_code=500, detail="Microsoft OAuth client_secret not configured")
        res_redirect = await db.run(get_config_request("Hostname"))
        if not res_redirect.rows:
          raise HTTPException(status_code=500, detail="Microsoft OAuth redirect URI not configured")
        redirect_uri = res_redirect.rows[0]["value"]
        id_token, access_token = await oauth.exchange_code_for_tokens(
          payload.code,
          client_id,
          client_secret,
          redirect_uri,
          payload.provider,
        )
        if not id_token:
          raise HTTPException(status_code=400, detail="Missing id_token")
      else:
        if not payload.id_token or not payload.access_token:
          raise HTTPException(status_code=400, detail="id_token and access_token required")
        id_token, access_token = payload.id_token, payload.access_token
    else:
      raise HTTPException(status_code=400, detail="Unsupported auth provider")
    _, profile, _ = await auth.handle_auth_login(payload.provider, id_token, access_token)
  set_request = set_provider_request(guid=auth_ctx.user_guid, provider=payload.provider)
  await db.run(set_request)
  if profile:
    raw_email = (profile.get("email") or "").strip()
    raw_name = (profile.get("username") or "").strip()
    email = raw_email
    display_name = raw_name or (raw_email.split("@")[0] if raw_email else "User")
    update_request = update_if_unedited_request(
      guid=auth_ctx.user_guid,
      email=email,
      display_name=display_name,
    )
    await db.run(update_request)
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
  oauth: OauthModule = request.app.state.oauth
  if payload.provider == "google":
    if not payload.code:
      raise HTTPException(status_code=400, detail="code required")
    google_provider = getattr(auth, "providers", {}).get("google")
    if not google_provider or not google_provider.audience:
      raise HTTPException(status_code=500, detail="Google OAuth client_id not configured")
    client_id = google_provider.audience
    env = request.app.state.env
    client_secret = env.get("GOOGLE_AUTH_SECRET")
    if not client_secret:
      raise HTTPException(status_code=500, detail="Google OAuth client_secret not configured")
    res_redirect = await db.run(get_config_request("Hostname"))
    if not res_redirect.rows:
      raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
    redirect_uri = res_redirect.rows[0]["value"]
    id_token, access_token = await oauth.exchange_code_for_tokens(
      payload.code,
      client_id,
      client_secret,
      redirect_uri,
      payload.provider,
    )
    if not id_token:
      raise HTTPException(status_code=400, detail="Missing id_token")
  elif payload.provider == "discord":
    discord_provider = getattr(auth, "providers", {}).get("discord")
    if not discord_provider or not getattr(discord_provider, "audience", None):
      raise HTTPException(status_code=500, detail="Discord OAuth client_id not configured")
    if payload.code:
      client_id = getattr(discord_provider, "audience")
      env = request.app.state.env
      client_secret = env.get("DISCORD_AUTH_SECRET")
      if not client_secret:
        raise HTTPException(status_code=500, detail="Discord OAuth client_secret not configured")
      res_redirect = await db.run(get_config_request("Hostname"))
      if not res_redirect.rows:
        raise HTTPException(status_code=500, detail="Discord OAuth redirect URI not configured")
      redirect_uri = res_redirect.rows[0]["value"]
      id_token, access_token = await oauth.exchange_code_for_tokens(
        payload.code,
        client_id,
        client_secret,
        redirect_uri,
        payload.provider,
      )
    else:
      if not payload.access_token:
        raise HTTPException(status_code=400, detail="access_token required")
      id_token = payload.id_token
      access_token = payload.access_token
  elif payload.provider == "microsoft":
    ms_provider = getattr(auth, "providers", {}).get("microsoft")
    if not ms_provider or not ms_provider.audience:
      raise HTTPException(status_code=500, detail="Microsoft OAuth client_id not configured")
    if payload.code:
      client_id = ms_provider.audience
      env = request.app.state.env
      client_secret = env.get("MICROSOFT_AUTH_SECRET")
      if not client_secret:
        raise HTTPException(status_code=500, detail="Microsoft OAuth client_secret not configured")
      res_redirect = await db.run(get_config_request("Hostname"))
      if not res_redirect.rows:
        raise HTTPException(status_code=500, detail="Microsoft OAuth redirect URI not configured")
      redirect_uri = res_redirect.rows[0]["value"]
      id_token, access_token = await oauth.exchange_code_for_tokens(
        payload.code,
        client_id,
        client_secret,
        redirect_uri,
        payload.provider,
      )
      if not id_token:
        raise HTTPException(status_code=400, detail="Missing id_token")
    else:
      if not payload.id_token or not payload.access_token:
        raise HTTPException(status_code=400, detail="id_token and access_token required")
      id_token = payload.id_token
      access_token = payload.access_token
  else:
    raise HTTPException(status_code=400, detail="Unsupported auth provider")
  provider_uid, _, _ = await auth.handle_auth_login(payload.provider, id_token, access_token)
  provider_uid = normalize_provider_identifier(provider_uid)
  request_db = get_by_provider_identifier_request(
    provider=payload.provider,
    provider_identifier=provider_uid,
  )
  res = await db.run(request_db)
  if res.rows and res.rows[0].get("guid") != auth_ctx.user_guid:
    raise HTTPException(status_code=409, detail="Provider already linked")
  link_request = link_provider_request(
    guid=auth_ctx.user_guid,
    provider=payload.provider,
    provider_identifier=provider_uid,
  )
  await db.run(link_request)
  return RPCResponse(op=rpc_request.op, payload={"provider": payload.provider}, version=rpc_request.version)

async def users_providers_unlink_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersUnlinkProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  profile_request = get_profile_request(guid=auth_ctx.user_guid)
  res_prof = await db.run(profile_request)
  default_provider = res_prof.rows[0].get("default_provider") if res_prof.rows else None
  unlink_request = unlink_provider_request(
    guid=auth_ctx.user_guid,
    provider=payload.provider,
  )
  res = await db.run(unlink_request)
  remaining = res.rows[0].get("providers_remaining") if res.rows else 0
  if remaining == 0:
    final_unlink_request = unlink_last_provider_request(
      guid=auth_ctx.user_guid,
      provider=payload.provider,
    )
    await db.run(final_unlink_request)
  elif payload.provider == default_provider:
    if not payload.new_default:
      raise HTTPException(status_code=400, detail="new_default required")
    set_request = set_provider_request(
      guid=auth_ctx.user_guid,
      provider=payload.new_default,
    )
    await db.run(set_request)
    revoke_request = revoke_provider_tokens_request(
      guid=auth_ctx.user_guid,
      provider=payload.provider,
    )
    await db.run(revoke_request)
  return RPCResponse(op=rpc_request.op, payload={"provider": payload.provider}, version=rpc_request.version)

async def users_providers_get_by_provider_identifier_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersGetByProviderIdentifier1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  lookup_request = get_by_provider_identifier_request(
    provider=payload.provider,
    provider_identifier=payload.provider_identifier,
  )
  res = await db.run(lookup_request)
  row = res.rows[0] if res.rows else None
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)

async def users_providers_create_from_provider_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersCreateFromProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  email_request = get_user_by_email_request(email=payload.provider_email)
  res = await db.run(email_request)
  if res.rows:
    raise HTTPException(status_code=409, detail="Email already registered")
  create_request = create_from_provider_request(
    provider=payload.provider,
    provider_identifier=payload.provider_identifier,
    provider_email=payload.provider_email,
    provider_displayname=payload.provider_displayname,
    provider_profile_image=payload.provider_profile_image,
  )
  res = await db.run(create_request)
  row = res.rows[0] if res.rows else None
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)

