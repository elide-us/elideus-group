from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from rpc.helpers import is_secure_request, unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING

from .models import (
  AuthSessionGetSessionResponse1,
  AuthSessionGetTokenRequest1,
  AuthSessionGetTokenResponse1,
  AuthSessionOkResponse1,
  AuthSessionRefreshTokenRequest1,
  AuthSessionRefreshTokenResponse1,
)

if TYPE_CHECKING:
  from server.modules.session_module import SessionModule


async def auth_session_get_token_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = AuthSessionGetTokenRequest1(**(rpc_request.payload or {}))

  module: 'SessionModule' = request.app.state.session
  await module.on_ready()

  session_token, rotation_token, rot_exp, profile = await module.issue_token(
    payload.provider,
    payload.id_token,
    payload.access_token,
    payload.fingerprint,
    request.headers.get("user-agent"),
    request.client.host if request.client else None,
    payload.confirm,
    payload.reauthToken,
  )

  response_payload = AuthSessionGetTokenResponse1(token=session_token, profile=profile)
  rpc_resp = RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)
  response = JSONResponse(content=jsonable_encoder(rpc_resp))
  response.set_cookie(
    "rotation_token",
    rotation_token,
    httponly=True,
    secure=is_secure_request(request),
    samesite="lax",
    expires=rot_exp,
  )
  return response


async def auth_session_refresh_token_v1(request: Request):
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  payload = AuthSessionRefreshTokenRequest1(**(rpc_request.payload or {}))
  rotation_token = request.cookies.get("rotation_token")
  if not rotation_token:
    raise HTTPException(status_code=401, detail="Missing rotation token")
  module: 'SessionModule' = request.app.state.session
  await module.on_ready()
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token = await module.refresh_token(
    rotation_token,
    payload.fingerprint,
    user_agent,
    ip_address,
  )
  response_payload = AuthSessionRefreshTokenResponse1(token=session_token)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def auth_session_invalidate_token_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=401, detail="Missing or invalid session token")
  module: 'SessionModule' = request.app.state.session
  await module.on_ready()
  await module.invalidate_token(auth_ctx.user_guid)
  response_payload = AuthSessionOkResponse1()
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def auth_session_logout_device_v1(request: Request):
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  header = request.headers.get("authorization")
  if not header or not header.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
  token = header.split(" ", 1)[1].strip()
  module: 'SessionModule' = request.app.state.session
  await module.on_ready()
  await module.logout_device(token)
  response_payload = AuthSessionOkResponse1()
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def auth_session_get_session_v1(request: Request):
  rpc_request, _auth_ctx, _ = await unbox_request(request)
  header = request.headers.get("authorization")
  if not header or not header.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
  token = header.split(" ", 1)[1].strip()
  module: 'SessionModule' = request.app.state.session
  await module.on_ready()
  ip_address = request.client.host if request.client else None
  user_agent = request.headers.get("user-agent")
  payload = await module.get_session(token, ip_address, user_agent)
  response_payload = AuthSessionGetSessionResponse1(**payload)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)
