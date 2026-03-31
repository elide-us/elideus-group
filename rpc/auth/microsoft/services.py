from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from rpc.helpers import is_secure_request, unbox_request
from server.models import RPCResponse
from server.modules.oauth_module import OauthModule
from .models import AuthMicrosoftOauthLogin1, AuthMicrosoftOauthLoginPayload1


async def auth_microsoft_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = AuthMicrosoftOauthLoginPayload1(**(rpc_request.payload or {}))

  module: OauthModule = request.app.state.oauth
  await module.on_ready()

  result = await module.login_provider(
    payload.provider,
    id_token=payload.idToken or payload.id_token,
    access_token=payload.accessToken or payload.access_token,
    fingerprint=payload.fingerprint,
    confirm=payload.confirm,
    reauth_token=payload.reAuthToken,
    user_agent=request.headers.get("user-agent"),
    ip_address=request.client.host if request.client else None,
  )

  user = result["user"]
  response_payload = AuthMicrosoftOauthLogin1(
    sessionToken=result["session_token"],
    display_name=user["display_name"],
    credits=user["credits"],
    profile_image=user.get("profile_image"),
  )
  rpc_resp = RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)
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
