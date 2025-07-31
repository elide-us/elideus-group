import logging

from fastapi import Request

from rpc.auth.microsoft.models import AuthMicrosoftLoginData1
from rpc.helpers import get_rpcrequest_from_request, mask_to_names
from rpc.models import RPCRequest, RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.mssql_module import MSSQLModule, _utos


async def user_login_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  req_payload = rpc_request.payload or {}
  auth: AuthModule = request.app.state.auth
  db: MSSQLModule = request.app.state.mssql

  provider = req_payload.get("provider", "microsoft")
  logging.debug("user_login_v1 provider=%s", provider)
  id_token = req_payload.get("idToken")
  access_token = req_payload.get("accessToken")
  data = await auth.verify_ms_id_token(id_token)
  guid = data.get("sub")
  user = await db.select_user(provider, guid)
  profile = await auth.fetch_ms_user_profile(access_token)
  profile_picture = profile.get("profilePicture")
  if not user:
    user = await db.insert_user(provider, guid, profile["email"], profile["username"])
  if profile_picture:
    await db.set_user_profile_image(_utos(user["guid"]), profile_picture)
  else:
    profile_picture = user.get("profile_image")
  logging.debug("user_login_v1 user=%s", user)

  token = auth.make_bearer_token(_utos(user["guid"]))
  rotation_token, rotation_exp = auth.make_rotation_token(_utos(user["guid"]))
  await db.create_user_session(_utos(user["guid"]), token, rotation_token, rotation_exp)

  discord = getattr(request.app.state, 'discord', None)
  if discord:
    mask = await db.get_user_roles(_utos(user["guid"]))
    names = mask_to_names(mask)
    roles = ", ".join(names) if names else "None"
    msg = (
      f"User login {_utos(user['guid'])}: {user.get('display_name')} "
      f"Credits: {user.get('credits', 0)} Roles: {roles}"
    )
    await discord.send_sys_message(msg)

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
