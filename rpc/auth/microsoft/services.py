from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from rpc.helpers import is_secure_request, unbox_request
from server.models import RPCResponse
from server.modules.oauth_module import OauthModule
from .models import AuthMicrosoftOauthLogin1


async def auth_microsoft_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  req_payload = rpc_request.payload or {}

  module: OauthModule = request.app.state.oauth
  await module.on_ready()

  result = await module.login_provider(
    req_payload.get("provider", "microsoft"),
    id_token=req_payload.get("idToken") or req_payload.get("id_token"),
    access_token=req_payload.get("accessToken") or req_payload.get("access_token"),
    fingerprint=req_payload.get("fingerprint"),
    confirm=req_payload.get("confirm"),
    reauth_token=req_payload.get("reauthToken") or req_payload.get("reAuthToken"),
    user_agent=request.headers.get("user-agent"),
    ip_address=request.client.host if request.client else None,
  )

  user = result["user"]
  payload = AuthMicrosoftOauthLogin1(
    sessionToken=result["session_token"],
    display_name=user["display_name"],
    credits=user["credits"],
    profile_image=user.get("profile_image"),
  )
  rpc_resp = RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
  response = JSONResponse(content=jsonable_encoder(rpc_resp))
  response.set_cookie(
    "rotation_token",
    result["rotation_token"],
    httponly=True,
    secure=is_secure_request(request),
    samesite="lax",
    expires=result["rotation_exp"],
  )
  return response
