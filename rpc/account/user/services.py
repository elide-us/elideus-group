from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.user_admin_module import UserAdminModule
from .models import (
  AccountUserGuid1,
  AccountUserSetCredits1,
  AccountUserStorageStatus1,
)


async def account_user_get_profile_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  user_admin: UserAdminModule = request.app.state.user_admin
  profile = await user_admin.get_profile(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=profile.model_dump(),
    version=rpc_request.version,
  )


async def account_user_set_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserSetCredits1(**(rpc_request.payload or {}))
  user_admin: UserAdminModule = request.app.state.user_admin
  await user_admin.set_credits(data.userGuid, data.credits)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def account_user_reset_display_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  user_admin: UserAdminModule = request.app.state.user_admin
  await user_admin.reset_display(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def account_user_enable_storage_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  user_admin: UserAdminModule = request.app.state.user_admin
  await user_admin.enable_storage(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def account_user_check_storage_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  user_admin: UserAdminModule = request.app.state.user_admin
  exists = await user_admin.check_storage(data.userGuid)
  status = AccountUserStorageStatus1(userGuid=data.userGuid, exists=exists)
  return RPCResponse(
    op=rpc_request.op,
    payload=status.model_dump(),
    version=rpc_request.version,
  )
