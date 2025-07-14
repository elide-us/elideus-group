from fastapi import Request
from rpc.models import RPCResponse, RPCRequest
from rpc.auth.microsoft.models import AuthMicrosoftLoginData1
from server.modules.auth_module import AuthModule
from server.modules.database_module import DatabaseModule, _utos

async def user_login_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  req_payload = rpc_request.payload or {}
  auth: AuthModule = request.app.state.auth
  db: DatabaseModule = request.app.state.database

  guid, profile = await auth.handle_ms_auth_login(
    req_payload.get("idToken"),
    req_payload.get("accessToken"),
  )

  user = await db.select_ms_user(guid)
  if not user:
    user = await db.insert_ms_user(guid, profile["email"], profile["username"])

  #token = auth.make_bearer_token(user["guid"])
  token = auth.make_bearer_token(_utos(user["guid"]))


  payload = AuthMicrosoftLoginData1(
    bearerToken=token,
    defaultProvider=user.get("provider_name", "microsoft"),
    username=user.get("username", profile["username"]),
    email=user.get("email", profile["email"]),
    backupEmail=user.get("backup_email"),
    profilePicture=profile.get("profilePicture"),
    credits=user.get("credits", 0),
  )
  return RPCResponse(op="urn:auth:microsoft:login_data:1", payload=payload, version=1)
