from fastapi import Request
import logging
from rpc.models import RPCResponse, RPCRequest
from rpc.auth.google.models import AuthGoogleLoginData1
from server.modules.auth_module import AuthModule
from server.modules.database_provider import DatabaseProvider, _utos
from server.helpers.roles import mask_to_names

async def user_login_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  req_payload = rpc_request.payload or {}
  auth: AuthModule = request.app.state.auth
  db: DatabaseProvider = request.app.state.mssql
  logging.debug(
    "user_login_v1 payload=%s",
    req_payload,
  )

  provider = "google"
  id_token = req_payload.get("idToken")
  access_token = req_payload.get("accessToken")
  guid, profile = await auth.handle_auth_login(provider, id_token, access_token)
  user = await db.select_user(provider, guid)
  profile_picture = profile.get("profilePicture")
  if not user:
    user = await db.insert_user(provider, guid, profile["email"], profile["username"])
  if profile_picture:
    await db.set_user_profile_image(
      _utos(user["guid"]),
      profile_picture,
      provider,
    )
  else:
    profile_picture = user.get("profile_image")

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

  payload = AuthGoogleLoginData1(
    bearerToken=token,
    defaultProvider=user.get("provider_name", provider),
    username=user.get("display_name", profile.get("username", "")),
    email=user.get("email", profile.get("email", "")),
    backupEmail=None,
    profilePicture=profile_picture,
    credits=user.get("credits", 0),
    rotationToken=rotation_token,
    rotationExpires=rotation_exp,
  )
  return RPCResponse(op="urn:auth:google:login_data:1", payload=payload, version=1)
