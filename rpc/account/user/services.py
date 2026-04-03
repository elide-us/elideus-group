from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from .models import (
  AccountUserCreateFolder1,
  AccountUserCredits1,
  AccountUserDisplayName1,
  AccountUserGuid1,
  AccountUserSetCredits1,
)

if TYPE_CHECKING:
  from server.modules.storage_module import StorageModule
  from server.modules.user_admin_module import UserAdminModule


async def account_user_get_displayname_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.on_ready()

  result: AccountUserDisplayName1 = await module.get_displayname(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def account_user_get_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.on_ready()

  result: AccountUserCredits1 = await module.get_credits(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def account_user_set_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserSetCredits1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.on_ready()

  await module.set_credits(data.userGuid, data.credits)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def account_user_reset_display_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserGuid1(**(rpc_request.payload or {}))
  module: UserAdminModule = request.app.state.user_admin
  await module.on_ready()

  await module.reset_display(data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def account_user_create_folder_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountUserCreateFolder1(**(rpc_request.payload or {}))
  module: StorageModule = request.app.state.storage
  await module.on_ready()

  await module.create_user_folder(data.userGuid, data.path)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
