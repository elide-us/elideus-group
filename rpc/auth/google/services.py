import logging, uuid

from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.env_module import EnvModule
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from server.modules.oauth_module import OauthModule
from .models import AuthGoogleOauthLogin1, AuthGoogleOauthLoginPayload1
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def normalize_provider_identifier(pid: str) -> str:
  try:
    return str(uuid.UUID(pid))
  except ValueError:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, pid))


async def auth_google_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    req_payload = AuthGoogleOauthLoginPayload1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

  provider = req_payload.provider
  code = req_payload.code
  confirm = req_payload.confirm
  reauth_token = req_payload.reauthToken or (rpc_request.payload or {}).get("reAuthToken")
  logging.debug(f"[auth_google_oauth_login_v1] provider={provider}")
  logging.debug(
    f"[auth_google_oauth_login_v1] code={code[:40] if code else None}"
  )

  env: EnvModule = request.app.state.env
  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db
  oauth: OauthModule = request.app.state.oauth

  # Get provider metadata
  google_provider = getattr(auth, "providers", {}).get("google")

  # Require Google client_id from provider config
  if not google_provider or not google_provider.audience:
      raise HTTPException(status_code=500, detail="Google OAuth client_id not configured")
  client_id = google_provider.audience

  # Acquire client_secret from environment
  client_secret = env.get("GOOGLE_AUTH_SECRET")
  if not client_secret:
    raise HTTPException(status_code=500, detail="GOOGLE_AUTH_SECRET not configured")

  # Require redirect_uri from system config
  res_redirect = await db.run("db:system:config:get_config:1", {"key": "Hostname"})
  if not res_redirect.rows:
      raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
  redirect_uri = res_redirect.rows[0]["value"]
  logging.debug("[auth_google_oauth_login_v1] GoogleClientId=%s", client_id)
  logging.debug("[auth_google_oauth_login_v1] redirect_uri=%s", redirect_uri)

  id_token, access_token = await oauth.exchange_code_for_tokens(
    code,
    client_id,
    client_secret,
    redirect_uri,
  )

  provider_uid, profile, payload = await auth.handle_auth_login(
    provider, id_token, access_token
  )
  provider_uid = normalize_provider_identifier(provider_uid)
  logging.debug(
    f"[auth_google_oauth_login_v1] provider_uid={provider_uid[:40] if provider_uid else None}"
  )

  identifiers = oauth.extract_identifiers(provider_uid, payload)
  user = await oauth.lookup_user(provider, identifiers)

  if user and user.get("element_soft_deleted_at"):
    res = await db.run(
      f"db:auth:{provider}:oauth_relink:1",
      {
        "provider_identifier": provider_uid,
        "email": profile["email"],
        "display_name": profile["username"],
        "profile_image": profile.get("profilePicture"),
        "confirm": confirm,
        "reauth_token": reauth_token,
      },
    )
    user = res.rows[0] if res.rows else None

  if not user:
    res = await db.run(
      "db:users:providers:get_any_by_provider_identifier:1",
      {"provider": provider, "provider_identifier": provider_uid},
    )
    if res.rows:
      res2 = await db.run(
        f"db:auth:{provider}:oauth_relink:1",
        {
          "provider_identifier": provider_uid,
          "email": profile["email"],
          "display_name": profile["username"],
          "profile_image": profile.get("profilePicture"),
          "confirm": confirm,
          "reauth_token": reauth_token,
        },
      )
      user = res2.rows[0] if res2.rows else None

  if not user:
    res = await db.run(
      f"db:auth:{provider}:oauth_relink:1",
      {
        "provider_identifier": provider_uid,
        "email": profile["email"],
        "display_name": profile["username"],
        "profile_image": profile.get("profilePicture"),
        "confirm": confirm,
        "reauth_token": reauth_token,
      },
    )
    user = res.rows[0] if res.rows else None

  if not user:
    logging.debug("[auth_google_oauth_login_v1] user not found, creating new user")
    res = await db.run(
      "db:users:providers:create_from_provider:1",
      {
        "provider": provider,
        "provider_identifier": provider_uid,
        "provider_email": profile["email"],
        "provider_displayname": profile["username"],
        "provider_profile_image": profile.get("profilePicture"),
      },
    )
    user = res.rows[0] if res.rows else None
    if not user:
      logging.debug("[auth_google_oauth_login_v1] fetching user after creation")
      res = await db.run(
        "db:users:providers:get_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": provider_uid},
      )
      user = res.rows[0] if res.rows else None
    if not user:
      logging.debug("[auth_google_oauth_login_v1] failed to create user")
      raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]
  new_img = profile.get("profilePicture")
  if new_img and new_img != user.get("profile_image"):
    await db.run(
      "db:users:profile:set_profile_image:1",
      {"guid": user_guid, "image_b64": new_img, "provider": provider},
    )
    user["profile_image"] = new_img
  if user.get("provider_name") == "google":
    res_prof = await db.run(
      "db:users:profile:update_if_unedited:1",
      {
        "guid": user_guid,
        "email": profile["email"],
        "display_name": profile["username"],
      },
    )
    if res_prof.rows:
      updated = res_prof.rows[0]
      if updated.get("display_name"):
        user["display_name"] = updated["display_name"]
      if updated.get("email"):
        user["email"] = updated["email"]
  fingerprint = req_payload.fingerprint
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token, session_exp, rotation_token, rot_exp = await oauth.create_session(
    user_guid, provider, fingerprint, user_agent, ip_address
  )

  payload = AuthGoogleOauthLogin1(
    sessionToken=session_token,
    display_name=user["display_name"],
    credits=user["credits"],
    profile_image=user.get("profile_image"),
  )
  rpc_resp = RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
  response = JSONResponse(content=jsonable_encoder(rpc_resp))
  response.set_cookie(
    "rotation_token",
    rotation_token,
    httponly=True,
    secure=True,
    samesite="lax",
    expires=rot_exp,
  )
  return response
