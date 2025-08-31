from datetime import datetime, timezone
import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uuid

from rpc.helpers import unbox_request
from server.models import RPCResponse
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

  provider_uid, provider_profile, payload = await auth.handle_auth_login(provider, id_token, access_token)

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

  def _norm(pid: str) -> str | None:
    try:
      return str(uuid.UUID(pid))
    except ValueError:
      try:
        import base64
        pad = pid + "=" * (-len(pid) % 4)
        raw = base64.urlsafe_b64decode(pad)
        if len(raw) >= 16:
          return str(uuid.UUID(bytes=raw[-16:]))
      except Exception:
        return None
    return None

  user = None
  checked = set()
  for pid in identifiers:
    uid = _norm(pid)
    if not uid or uid in checked:
      continue
    checked.add(uid)
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
        "provider_email": provider_profile["email"],
        "provider_displayname": provider_profile["username"],
        "provider_profile_image": provider_profile.get("profilePicture"),
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

  new_img = provider_profile.get("profilePicture")
  if new_img and new_img != user.get("profile_image"):
    await db.run(
      "urn:users:profile:set_profile_image:1",
      {"guid": user["guid"], "image_b64": new_img, "provider": provider},
    )
    user["profile_image"] = new_img

  user_guid = user["guid"]
  rotation_token, rot_exp = auth.make_rotation_token(user_guid)
  now = datetime.now(timezone.utc)
  await db.run(
    "db:users:session:set_rotkey:1",
    {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
  )

  roles, _ = await auth.get_user_roles(user_guid)
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
      "provider": provider,
    },
  )

  profile = {
    "display_name": user["display_name"],
    "email": user.get("email"),
    "credits": user.get("credits"),
    "profile_image": user.get("profile_image"),
  }
  payload = {"token": session_token, "profile": profile}
  rpc_resp = RPCResponse(op="urn:auth:session:get_token:1", payload=payload, version=1)
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

async def auth_session_refresh_token_v1(request: Request):
  rotation_token = request.cookies.get("rotation_token")
  if not rotation_token:
    raise HTTPException(status_code=401, detail="Missing rotation token")

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  data = auth.decode_rotation_token(rotation_token)
  user_guid = data["guid"]
  stored = await db.run("db:users:session:get_rotkey:1", {"guid": user_guid})
  row = stored.rows[0] if stored.rows else None
  if not row or row.get("rotkey") != rotation_token:
    raise HTTPException(status_code=401, detail="Invalid rotation token")

  provider = row.get("provider_name") or "microsoft"
  roles, _ = await auth.get_user_roles(user_guid)
  session_token, _ = auth.make_session_token(user_guid, rotation_token, roles, provider)
  return RPCResponse(op="urn:auth:session:refresh_token:1", payload={"token": session_token}, version=1)

async def auth_session_invalidate_token_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
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


async def auth_session_logout_device_v1(request: Request):
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  header = request.headers.get("authorization")
  if not header or not header.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
  token = header.split(" ", 1)[1].strip()

  db: DbModule = request.app.state.db
  await db.run("db:auth:session:revoke_device_token:1", {"access_token": token})
  return RPCResponse(op=rpc_request.op, payload={"ok": True}, version=rpc_request.version)


async def auth_session_get_session_v1(request: Request):
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  header = request.headers.get("authorization")
  if not header or not header.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
  token = header.split(" ", 1)[1].strip()

  db: DbModule = request.app.state.db
  res = await db.run("db:auth:session:get_by_access_token:1", {"access_token": token})
  session = res.rows[0] if res.rows else None
  if not session:
    raise HTTPException(status_code=401, detail="Invalid session token")

  if session.get("revoked_at"):
    raise HTTPException(status_code=401, detail="Session revoked")

  expires_at = session.get("expires_at")
  if expires_at:
    try:
      exp_dt = datetime.fromisoformat(expires_at)
    except ValueError:
      exp_dt = None
    if exp_dt and exp_dt.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
      raise HTTPException(status_code=401, detail="Session expired")
  ip_address = request.client.host if request.client else None
  user_agent = request.headers.get("user-agent")
  try:
    await db.run(
      "db:auth:session:update_session:1",
      {"access_token": token, "ip_address": ip_address, "user_agent": user_agent},
    )
  except Exception as e:
    logging.error("[auth_session_get_session_v1] Failed to update session metadata: %s", e)

  payload = {
    "session_guid": session.get("session_guid"),
    "device_guid": session.get("device_guid"),
    "user_guid": session.get("user_guid"),
    "issued_at": session.get("issued_at"),
    "expires_at": session.get("expires_at"),
    "device_fingerprint": session.get("device_fingerprint"),
    "user_agent": session.get("user_agent"),
    "ip_last_seen": session.get("ip_last_seen"),
  }
  return RPCResponse(op=rpc_request.op, payload=payload, version=rpc_request.version)

