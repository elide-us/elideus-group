from datetime import datetime, timezone

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import uuid

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule

async def auth_session_get_token_v1(request: Request):
  body = await request.json()
  provider = body.get("provider")
  id_token = body.get("id_token")
  access_token = body.get("access_token")
  if not provider or not id_token or not access_token:
    raise HTTPException(status_code=400, detail="Missing credentials")

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  provider_uid, profile, payload = await auth.handle_auth_login(provider, id_token, access_token)

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
      import base64
      home_account_id = base64.urlsafe_b64encode(b"\x00" * 16 + uuid.UUID(base_id).bytes).decode("utf-8").rstrip("=")
      if home_account_id not in identifiers:
        identifiers.append(home_account_id)
    except Exception:
      pass

  user = None
  for pid in identifiers:
    try:
      uid = str(uuid.UUID(pid))
    except ValueError:
      continue
    res = await db.run(
      "urn:users:providers:get_by_provider_identifier:1",
      {"provider": provider, "provider_identifier": uid},
    )
    if res.rows:
      user = res.rows[0]
      break

  if not user:
    try:
      provider_uid = str(uuid.UUID(provider_uid))
    except ValueError:
      raise HTTPException(status_code=400, detail="Invalid provider identifier")
    res = await db.run(
      "urn:users:providers:create_from_provider:1",
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
      res = await db.run(
        "urn:users:providers:get_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": provider_uid},
      )
      user = res.rows[0] if res.rows else None
  if not user:
    raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]
  rotation_token, rot_exp = auth.make_rotation_token(user_guid)
  now = datetime.now(timezone.utc)
  await db.run(
    "db:users:session:set_rotkey:1",
    {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
  )

  roles_res = await db.run("urn:users:profile:get_roles:1", {"guid": user_guid})
  role_mask = int(roles_res.rows[0].get("element_roles", 0)) if roles_res.rows else 0
  authz = request.app.state.authz
  roles = authz.mask_to_names(role_mask)

  session_token, session_exp = auth.make_session_token(user_guid, rotation_token, roles, provider)

  fingerprint = body.get("fingerprint")
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

  payload = {"token": session_token, "profile": profile}
  rpc_resp = RPCResponse(op="urn:auth:session:get_token:1", payload=payload, version=1)
  response = JSONResponse(content=rpc_resp.model_dump())
  response.set_cookie(
    "rotation_token",
    rotation_token,
    httponly=True,
    secure=True,
    samesite="lax",
    expires=rot_exp,
  )
  return response

async def auth_session_refresh_token_v1(request: Request):
  rotation_token = request.cookies.get("rotation_token")
  if not rotation_token:
    raise HTTPException(status_code=401, detail="Missing rotation token")

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  data = auth.decode_rotation_token(rotation_token)
  user_guid = data["guid"]
  stored = await db.run("db:users:session:get_rotkey:1", {"guid": user_guid})
  if not stored.rows or stored.rows[0].get("rotkey") != rotation_token:
    raise HTTPException(status_code=401, detail="Invalid rotation token")

  roles_res = await db.run("urn:users:profile:get_roles:1", {"guid": user_guid})
  role_mask = int(roles_res.rows[0].get("element_roles", 0)) if roles_res.rows else 0
  authz = request.app.state.authz
  roles = authz.mask_to_names(role_mask)

  session_token, _ = auth.make_session_token(user_guid, rotation_token, roles, "microsoft")
  return RPCResponse(op="urn:auth:session:refresh_token:1", payload={"token": session_token}, version=1)

async def auth_session_invalidate_token_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  rotation_token = auth_ctx.claims.get("session")
  if not rotation_token or not auth_ctx.user_guid:
    raise HTTPException(status_code=401, detail="Missing or invalid session token")

  db: DbModule = request.app.state.db
  now = datetime.now(timezone.utc)
  await db.run(
    "db:users:session:set_rotkey:1",
    {"guid": auth_ctx.user_guid, "rotkey": "", "iat": now, "exp": now},
  )
  return RPCResponse(op=rpc_request.op, payload={"ok": True}, version=rpc_request.version)

