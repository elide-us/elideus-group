from fastapi import Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.user_admin_module import UserAdminModule
from .models import (
  AccountUserGuid1,
  AccountUserSetCredits1,
  AccountUserDisplayName1,
  AccountUserCredits1,
)


async def account_user_get_displayname_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  user_admin: UserAdminModule = request.app.state.user_admin
  display = await user_admin.get_displayname(data.userGuid)
  res = AccountUserDisplayName1(userGuid=data.userGuid, displayName=display)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def account_user_get_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  user_admin: UserAdminModule = request.app.state.user_admin
  credits = await user_admin.get_credits(data.userGuid)
  res = AccountUserCredits1(userGuid=data.userGuid, credits=credits)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
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
