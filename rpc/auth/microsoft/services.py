import base64, logging, uuid

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from server.modules.oauth_module import OauthModule
from .models import AuthMicrosoftOauthLogin1


def normalize_provider_identifier(pid: str) -> str:
  try:
    return str(uuid.UUID(pid))
  except ValueError:
    try:
      pad = pid + "=" * (-len(pid) % 4)
      raw = base64.urlsafe_b64decode(pad)
      if len(raw) >= 16:
        return str(uuid.UUID(bytes=raw[-16:]))
    except Exception:
      pass
    return str(uuid.uuid5(uuid.NAMESPACE_URL, pid))


async def auth_microsoft_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  req_payload = rpc_request.payload or {}

  provider = req_payload.get("provider", "microsoft")
  id_token = req_payload.get("idToken") or req_payload.get("id_token")
  access_token = req_payload.get("accessToken") or req_payload.get("access_token")
  logging.debug(f"[auth_microsoft_oauth_login_v1] provider={provider}")
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] id_token={id_token[:40] if id_token else None}"
  )
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] access_token={access_token[:40] if access_token else None}"
  )
  if not id_token or not access_token:
    raise HTTPException(status_code=400, detail="Missing credentials")

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db
  oauth: OauthModule = request.app.state.oauth

  provider_uid, profile, payload = await auth.handle_auth_login(
    provider, id_token, access_token
  )
  provider_uid = normalize_provider_identifier(provider_uid)
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] provider_uid={provider_uid[:40] if provider_uid else None}"
  )

  identifiers = oauth.extract_identifiers(provider_uid, payload, "microsoft")
  user = await oauth.lookup_user(provider, identifiers)

  if not user or user.get("element_soft_deleted_at"):
    res = await db.run(
      f"db:auth:{provider}:oauth_relink:1",
      {
        "provider_identifier": provider_uid,
        "email": profile["email"],
        "display_name": profile["username"],
        "profile_image": profile.get("profilePicture"),
        "confirm": req_payload.get("confirm"),
        "reauth_token": req_payload.get("reauthToken") or req_payload.get("reAuthToken"),
      },
    )
    user = res.rows[0] if res.rows else None

  if not user:
    logging.debug("[auth_microsoft_oauth_login_v1] user not found, creating new user")
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
      logging.debug("[auth_microsoft_oauth_login_v1] fetching user after creation")
      res = await db.run(
        "db:users:providers:get_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": provider_uid},
      )
      user = res.rows[0] if res.rows else None
    if not user:
      logging.debug("[auth_microsoft_oauth_login_v1] failed to create user")
      raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]
  new_img = profile.get("profilePicture")
  if new_img != user.get("profile_image"):
    await db.run(
      "db:users:profile:set_profile_image:1",
      {"guid": user_guid, "image_b64": new_img, "provider": provider},
    )
    user["profile_image"] = new_img
  if user.get("provider_name") == "microsoft":
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
  fingerprint = req_payload.get("fingerprint")
  if not fingerprint:
    raise HTTPException(status_code=400, detail="Missing fingerprint")
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token, session_exp, rotation_token, rot_exp = await oauth.create_session(
    user_guid, provider, fingerprint, user_agent, ip_address
  )

  payload = AuthMicrosoftOauthLogin1(
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

