from fastapi import Request
from rpc.models import RPCResponse, RPCRequest
from rpc.auth.microsoft.models import AuthMicrosoftLoginData1
from server.modules.auth_module import AuthModule

async def user_login_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  auth: AuthModule = request.app.state.modules.get_module("auth")

  guid, profile = await auth.handle_ms_auth_login(
    payload.get("idToken"),
    payload.get("accessToken"),
  )

  token = auth.make_bearer_token(guid)

  login_data = AuthMicrosoftLoginData1(
    bearerToken=token,
    defaultProvider="microsoft",
    username=profile["username"],
    email=profile["email"],
    backupEmail=payload.get("backupEmail"),
    profilePicture=profile.get("profilePicture"),
    credits=0,
  )

  return RPCResponse(op="urn:auth:microsoft:login_data:1", payload=login_data, version=1)
