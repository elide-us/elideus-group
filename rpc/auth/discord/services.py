from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from rpc.helpers import is_secure_request, unbox_request
from server.models import RPCResponse
from server.modules.oauth_module import OauthModule
from .models import AuthDiscordOauthLogin1, AuthDiscordOauthLoginPayload1


async def auth_discord_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    data = AuthDiscordOauthLoginPayload1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

  module: OauthModule = request.app.state.oauth
  await module.on_ready()

  result = await module.login_provider(
    data.provider,
    code=data.code,
    fingerprint=data.fingerprint,
    confirm=data.confirm,
    reauth_token=data.reauthToken,
    user_agent=request.headers.get("user-agent"),
    ip_address=request.client.host if request.client else None,
  )

  user = result["user"]
  payload = AuthDiscordOauthLogin1(
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
