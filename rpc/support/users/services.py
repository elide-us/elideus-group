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
  await module.on_ready()

  result: SupportUsersDisplayName1 = await module.get_displayname_for_support(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def support_users_get_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersGuid1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.on_ready()

  result: SupportUsersCredits1 = await module.get_credits_for_support(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def support_users_set_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersSetCredits1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.on_ready()

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
  await module.on_ready()

  await module.reset_display(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
