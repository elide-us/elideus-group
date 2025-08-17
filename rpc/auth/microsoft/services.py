from datetime import datetime, timezone
import base64, logging, uuid

from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.authz_module import AuthzModule
from server.modules.db_module import DbModule
from .models import AuthMicrosoftOauthLogin1


async def auth_microsoft_oauth_login_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  req_payload = rpc_request.payload or {}

  provider = req_payload.get("provider", "microsoft")
  id_token = req_payload.get("idToken") or req_payload.get("id_token")
  access_token = req_payload.get("accessToken") or req_payload.get("access_token")
  logging.debug(f"[auth_microsoft_oauth_login_v1] provider={provider}")
  logging.debug(f"[auth_microsoft_oauth_login_v1] id_token={id_token[:40] if id_token else None}")
  logging.debug(f"[auth_microsoft_oauth_login_v1] access_token={access_token[:40] if access_token else None}")
  if not id_token or not access_token:
    raise HTTPException(status_code=400, detail="Missing credentials")

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  provider_uid, profile, payload = await auth.handle_auth_login(provider, id_token, access_token)
  logging.debug(f"[auth_microsoft_oauth_login_v1] provider_uid={provider_uid[:40] if provider_uid else None}")

  identifiers = []
  if provider_uid:
    identifiers.append(provider_uid)
  oid = payload.get("oid")
  sub = payload.get("sub")
  if oid and oid not in identifiers:
    identifiers.append(oid)
  if sub and sub not in identifiers:
    identifiers.append(sub)

  base_id = oid or sub or provider_uid
  if base_id:
    try:
      home_account_id = base64.urlsafe_b64encode(b"\x00" * 16 + uuid.UUID(base_id).bytes).decode("utf-8").rstrip("=")
      if home_account_id not in identifiers:
        identifiers.append(home_account_id)
      logging.debug(f"[auth_microsoft_oauth_login_v1] home_account_id={home_account_id[:40]}")
    except Exception as e:
      logging.debug(f"[auth_microsoft_oauth_login_v1] home_account_id generation failed: {e}")

  user = None
  for pid in identifiers:
    logging.debug(f"[auth_microsoft_oauth_login_v1] checking identifier={pid[:40]}")
    res = await db.run(
      "urn:users:providers:get_by_provider_identifier:1",
      {"provider": provider, "provider_identifier": pid},
    )
    if res.rows:
      user = res.rows[0]
      logging.debug(f"[auth_microsoft_oauth_login_v1] user found with identifier={pid[:40]}")
      break

  if not user:
    logging.debug("[auth_microsoft_oauth_login_v1] user not found, creating new user")
    res = await db.run(
      "urn:users:providers:create_from_provider:1",
      {
        "provider": provider,
        "provider_identifier": provider_uid,
        "provider_email": profile["email"],
        "provider_displayname": profile["username"],
      },
    )
    user = res.rows[0] if res.rows else None
  if not user:
    logging.debug("[auth_microsoft_oauth_login_v1] failed to create user")
    raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]

  if profile.get("profilePicture"):
    await db.run(
      "urn:users:profile:set_profile_image:1",
      {"guid": user_guid, "image_b64": profile["profilePicture"], "provider": provider},
    )
    user["profile_image"] = profile["profilePicture"]
  rotation_token, rot_exp = auth.make_rotation_token(user_guid)
  logging.debug(f"[auth_microsoft_oauth_login_v1] rotation_token={rotation_token[:40]}")
  now = datetime.now(timezone.utc)
  await db.run(
    "db:users:session:set_rotkey:1",
    {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
  )

  roles_res = await db.run("urn:users:profile:get_roles:1", {"guid": user_guid})
  role_mask = int(roles_res.rows[0].get("element_roles", 0)) if roles_res.rows else 0
  authz: AuthzModule = request.app.state.authz
  roles = authz.mask_to_names(role_mask)
  session_token, session_exp = auth.make_session_token(user_guid, rotation_token, roles, provider)
  logging.debug(f"[auth_microsoft_oauth_login_v1] session_token={session_token[:40]}")

  fingerprint = req_payload.get("fingerprint")
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  await db.run(
    "db:auth:session:create_session:1",
    {
      "access_token": session_token,
      "expires": session_exp,
      "fingerprint": fingerprint,
      "user_agent": user_agent,
      "ip_address": ip_address,
      "user_guid": user_guid,
    },
  )

  payload = AuthMicrosoftOauthLogin1(
    sessionToken=session_token,
    display_name=user["display_name"],
    credits=user["credits"],
    profile_image=user.get("profile_image"),
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

