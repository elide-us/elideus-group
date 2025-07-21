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
  id_token = req_payload.get("idToken")
  access_token = req_payload.get("accessToken")
  data = await auth.verify_ms_id_token(id_token)
  guid = data.get("sub")
  user = await db.select_user(provider, guid)
  profile = None
  profile_picture = None
  if not user:
    profile = await auth.fetch_ms_user_profile(access_token)
    user = await db.insert_user(provider, guid, profile["email"], profile["username"])
    profile_picture = profile.get("profilePicture")
    if profile_picture:
      await db.set_user_profile_image(_utos(user["guid"]), profile_picture)
  else:
    profile_picture = user.get("profile_image")
  logging.debug("user_login_v1 user=%s", user)

  token = auth.make_bearer_token(_utos(user["guid"]))
  rotation_token, rotation_exp = auth.make_rotation_token(_utos(user["guid"]))
  await db.set_user_rotation_token(_utos(user["guid"]), rotation_token, rotation_exp)
  await db.create_user_session(_utos(user["guid"]), token, rotation_token, rotation_exp)

  payload = AuthMicrosoftLoginData1(
    bearerToken=token,
    defaultProvider=user.get("provider_name", provider),
    username=user.get("display_name", profile["username"] if profile else ""),
    email=user.get("email", profile["email"] if profile else ""),
    backupEmail=None,
    profilePicture=profile_picture,
    credits=user.get("credits", 0),
    rotationToken=rotation_token,
    rotationExpires=rotation_exp,
  )
  return RPCResponse(op="urn:auth:microsoft:login_data:1", payload=payload, version=1)
