import logging

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
    req_payload = AuthDiscordOauthLoginPayload1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

  provider = req_payload.provider
  code = req_payload.code
  confirm = req_payload.confirm
  reauth_token = req_payload.reauthToken
  fingerprint = req_payload.fingerprint
  logging.debug(f"[auth_discord_oauth_login_v1] provider={provider}")
  logging.debug(
    f"[auth_discord_oauth_login_v1] code={code[:40] if code else None}"
  )

  oauth: OauthModule = request.app.state.oauth

  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  result = await oauth.login_provider(
    provider,
    code=code,
    fingerprint=fingerprint,
    confirm=confirm,
    reauth_token=reauth_token,
    user_agent=user_agent,
    ip_address=ip_address,
  )
  user = result["user"]
  session_token = result["session_token"]
  rotation_token = result["rotation_token"]
  rot_exp = result["rotation_exp"]

  payload = AuthDiscordOauthLogin1(
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
    secure=is_secure_request(request),
    samesite="lax",
    expires=rot_exp,
  )
  return response
