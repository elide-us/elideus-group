import logging

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

  provider = req_payload.get("provider", "microsoft")
  id_token = req_payload.get("idToken") or req_payload.get("id_token")
  access_token = req_payload.get("accessToken") or req_payload.get("access_token")
  confirm = req_payload.get("confirm")
  reauth_token = req_payload.get("reauthToken") or req_payload.get("reAuthToken")
  fingerprint = req_payload.get("fingerprint")
  logging.debug(f"[auth_microsoft_oauth_login_v1] provider={provider}")
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] id_token={id_token[:40] if id_token else None}"
  )
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] access_token={access_token[:40] if access_token else None}"
  )

  oauth: OauthModule = request.app.state.oauth

  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  result = await oauth.login_provider(
    provider,
    id_token=id_token,
    access_token=access_token,
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

  payload = AuthMicrosoftOauthLogin1(
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
