from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.profile_module import ProfileModule
from .models import (
  UsersProfileProfile1,
  UsersProfileSetDisplay1,
  UsersProfileSetOptin1,
  UsersProfileRoles1,
  UsersProfileSetProfileImage1,
)


"""User profile service helpers.

`auth_ctx.user_guid` is populated for authenticated RPC requests. These
functions assume this GUID exists, and raise a validation error if the
GUID is missing.
"""


async def users_profile_get_profile_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  profile: ProfileModule = request.app.state.profile
  record = await profile.get_profile(user_guid)
  if not record:
    raise HTTPException(status_code=404, detail="Profile not found")
  record["guid"] = str(record.get("guid", ""))
  auth_providers = record.get("auth_providers")
  if auth_providers is None:
    record["auth_providers"] = []
  elif not isinstance(auth_providers, list):
    raise HTTPException(status_code=500, detail="Invalid auth provider payload")
  profile_payload = UsersProfileProfile1(**record)
  return RPCResponse(
    op=rpc_request.op,
    payload=profile_payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_display_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  payload = UsersProfileSetDisplay1(**(rpc_request.payload or {}))
  profile: ProfileModule = request.app.state.profile
  await profile.set_display(user_guid, payload.display_name)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_optin_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  payload = UsersProfileSetOptin1(**(rpc_request.payload or {}))
  profile: ProfileModule = request.app.state.profile
  await profile.set_optin(user_guid, payload.display_email)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  profile: ProfileModule = request.app.state.profile
  roles = await profile.get_roles(user_guid)
  payload = UsersProfileRoles1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_profile_image_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  payload = UsersProfileSetProfileImage1(**(rpc_request.payload or {}))
  profile: ProfileModule = request.app.state.profile
  await profile.set_profile_image(
    user_guid,
    payload.provider,
    payload.image_b64,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

