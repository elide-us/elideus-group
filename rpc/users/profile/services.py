from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.user_profile_module import UserProfileModule
from .models import (
  UsersProfileSetDisplay1,
  UsersProfileSetOptin1,
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

  profile_mod: UserProfileModule = request.app.state.user_profile
  profile = await profile_mod.get_profile(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=profile.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_display_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  payload = UsersProfileSetDisplay1(**(rpc_request.payload or {}))
  profile_mod: UserProfileModule = request.app.state.user_profile
  await profile_mod.set_display(user_guid, payload.display_name)
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
  profile_mod: UserProfileModule = request.app.state.user_profile
  await profile_mod.set_optin(user_guid, payload.display_email)
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

  profile_mod: UserProfileModule = request.app.state.user_profile
  payload = await profile_mod.get_roles(user_guid)
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
  profile_mod: UserProfileModule = request.app.state.user_profile
  await profile_mod.set_profile_image(
    user_guid,
    payload.image_b64,
    payload.provider,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

