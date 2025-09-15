from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from server.modules.session_module import SessionModule


def _get_session_module(request: Request) -> 'SessionModule':
  return request.app.state.session

async def auth_session_get_token_v1(request: Request):
  body = await request.json()
  provider = body.get("provider")
  id_token = body.get("id_token")
  access_token = body.get("access_token")
  fingerprint = body.get("fingerprint")
  confirm = body.get("confirm")
  reauth_token = body.get("reauthToken") or body.get("reAuthToken")
  if not provider or not id_token or not access_token or not fingerprint:
    raise HTTPException(status_code=400, detail="Missing credentials or fingerprint")
  session_mod = _get_session_module(request)
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token, rotation_token, rot_exp, profile = await session_mod.issue_token(
    provider,
    id_token,
    access_token,
    fingerprint,
    user_agent,
    ip_address,
    confirm,
    reauth_token,
  )
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
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  req_payload = rpc_request.payload or {}
  fingerprint = req_payload.get("fingerprint")
  if not fingerprint:
    raise HTTPException(status_code=400, detail="Missing fingerprint")
  session_mod = _get_session_module(request)
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token = await session_mod.refresh_token(
    rotation_token,
    fingerprint,
    user_agent,
    ip_address,
  )
  return RPCResponse(op=rpc_request.op, payload={"token": session_token}, version=rpc_request.version)

async def auth_session_invalidate_token_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=401, detail="Missing or invalid session token")
  session_mod = _get_session_module(request)
  await session_mod.invalidate_token(auth_ctx.user_guid)
  return RPCResponse(op=rpc_request.op, payload={"ok": True}, version=rpc_request.version)

async def auth_session_logout_device_v1(request: Request):
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  header = request.headers.get("authorization")
  if not header or not header.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
  token = header.split(" ", 1)[1].strip()
  session_mod = _get_session_module(request)
  await session_mod.logout_device(token)
  return RPCResponse(op=rpc_request.op, payload={"ok": True}, version=rpc_request.version)

async def auth_session_get_session_v1(request: Request):
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  header = request.headers.get("authorization")
  if not header or not header.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
  token = header.split(" ", 1)[1].strip()
  session_mod = _get_session_module(request)
  ip_address = request.client.host if request.client else None
  user_agent = request.headers.get("user-agent")
  payload = await session_mod.get_session(token, ip_address, user_agent)
  return RPCResponse(op=rpc_request.op, payload=payload, version=rpc_request.version)
