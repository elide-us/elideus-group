from fastapi import Request
import logging
from rpc.models import RPCResponse, RPCRequest
from rpc.auth.microsoft.models import AuthMicrosoftLoginData1
from server.modules.auth_module import AuthModule
from server.modules.database_module import DatabaseModule, _utos

async def user_login_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  req_payload = rpc_request.payload or {}
  auth: AuthModule = request.app.state.auth
  db: DatabaseModule = request.app.state.database
  logging.debug(
    "user_login_v1 payload=%s",
    req_payload,
  )

  provider = req_payload.get("provider", "microsoft")
  logging.debug("user_login_v1 provider=%s", provider)
  guid, profile = await auth.handle_auth_login(
    provider,
    req_payload.get("idToken"),
    req_payload.get("accessToken"),
  )
  logging.debug(
    "user_login_v1 guid=%s profile=%s",
    guid,
    profile,
  )

  user = await db.select_user(provider, guid)
  if not user:
    user = await db.insert_user(provider, guid, profile["email"], profile["username"])
  logging.debug("user_login_v1 user=%s", user)

  token = auth.make_bearer_token(_utos(user["guid"]))
  rotation_token, rotation_exp = auth.make_rotation_token(_utos(user["guid"]))
  await db.set_user_rotation_token(_utos(user["guid"]), rotation_token, rotation_exp)
  await db.create_user_session(_utos(user["guid"]), token, rotation_token, rotation_exp)

  payload = AuthMicrosoftLoginData1(
    bearerToken=token,
    defaultProvider=user.get("provider_name", provider),
    username=user.get("display_name", profile["username"]),
    email=user.get("email", profile["email"]),
    backupEmail=None,
    profilePicture=profile.get("profilePicture"),
    credits=user.get("credits", 0),
    rotationToken=rotation_token,
    rotationExpires=rotation_exp,
  )
  return RPCResponse(op="urn:auth:microsoft:login_data:1", payload=payload, version=1)
