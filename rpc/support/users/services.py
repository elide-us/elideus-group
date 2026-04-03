from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  SupportUsersCredits1,
  SupportUsersDisplayName1,
  SupportUsersGuid1,
  SupportUsersSetCredits1,
)

if TYPE_CHECKING:
  from server.modules.user_admin_module import UserAdminModule


async def support_users_get_displayname_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersGuid1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  display = await module.get_displayname(data.userGuid)
  res = SupportUsersDisplayName1(userGuid=data.userGuid, displayName=display)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def support_users_get_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersGuid1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  credits = await module.get_credits(data.userGuid)
  res = SupportUsersCredits1(userGuid=data.userGuid, credits=credits)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def support_users_set_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersSetCredits1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.set_credits(data.userGuid, data.credits)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def support_users_reset_display_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersGuid1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.reset_display(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
