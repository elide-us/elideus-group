from datetime import datetime, timezone

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from rpc.helpers import mask_to_names
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.database_module import DatabaseModule

async def auth_session_get_token_v1(request: Request):
  body = await request.json()
  provider = body.get("provider")
  id_token = body.get("id_token")
  access_token = body.get("access_token")
  if not provider or not id_token or not access_token:
    raise HTTPException(status_code=400, detail="Missing credentials")

  auth: AuthModule = request.app.state.auth
  db: DatabaseModule = request.app.state.db

  provider_uid, profile = await auth.handle_auth_login(provider, id_token, access_token)

  res = await db.run(
    "urn:users:providers:get_by_provider_identifier:1",
    {"provider": provider, "provider_identifier": provider_uid},
  )
  user = res.rows[0] if res.rows else None
  if not user:
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
    raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]
  rotation_token, rot_exp = auth.make_rotation_token(user_guid)
  now = datetime.now(timezone.utc)
  await db.run(
    "urn:users:rotkey:set:1",
    {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
  )

  roles_res = await db.run("urn:users:profile:get_roles:1", {"guid": user_guid})
  role_mask = int(roles_res.rows[0].get("element_roles", 0)) if roles_res.rows else 0
  roles = mask_to_names(role_mask)

  session_token = auth.make_session_token(user_guid, rotation_token, roles, provider)

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
  db: DatabaseModule = request.app.state.db

  data = auth.decode_rotation_token(rotation_token)
  user_guid = data["guid"]
  stored = await db.run("urn:users:rotkey:get:1", {"guid": user_guid})
  if not stored.rows or stored.rows[0].get("rotkey") != rotation_token:
    raise HTTPException(status_code=401, detail="Invalid rotation token")

  roles_res = await db.run("urn:users:profile:get_roles:1", {"guid": user_guid})
  role_mask = int(roles_res.rows[0].get("element_roles", 0)) if roles_res.rows else 0
  roles = mask_to_names(role_mask)

  session_token = auth.make_session_token(user_guid, rotation_token, roles, "microsoft")
  return RPCResponse(op="urn:auth:session:refresh_token:1", payload={"token": session_token}, version=1)

async def auth_session_invalidate_token_v1(request: Request):
  rotation_token = request.cookies.get("rotation_token")
  if not rotation_token:
    raise HTTPException(status_code=400, detail="Missing rotation token")

  auth: AuthModule = request.app.state.auth
  db: DatabaseModule = request.app.state.db

  data = auth.decode_rotation_token(rotation_token)
  user_guid = data["guid"]
  now = datetime.now(timezone.utc)
  await db.run(
    "urn:users:rotkey:set:1",
    {"guid": user_guid, "rotkey": "", "iat": now, "exp": now},
  )
  resp = RPCResponse(op="urn:auth:session:invalidate_token:1", payload={"ok": True}, version=1)
  response = JSONResponse(content=resp.model_dump())
  response.delete_cookie("rotation_token")
  return response

