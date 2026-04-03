from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from .models import (
  AccountRoleAggregateList1,
  AccountRoleDeleteRole1,
  AccountRoleGetMembersRequest1,
  AccountRoleList1,
  AccountRoleMemberUpdate1,
  AccountRoleMembers1,
  AccountRoleUpsertRole1,
)

if TYPE_CHECKING:
  from server.modules.role_admin_module import RoleAdminModule


async def account_role_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: AccountRoleList1 = await module.list_roles(auth_ctx.role_mask)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def account_role_get_all_role_members_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: AccountRoleAggregateList1 = await module.get_all_role_members(auth_ctx.role_mask)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def account_role_get_role_members_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  input_payload = AccountRoleGetMembersRequest1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: AccountRoleMembers1 = await module.get_role_members(input_payload.role)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def account_role_add_role_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: AccountRoleMembers1 = await module.add_role_member(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def account_role_remove_role_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: AccountRoleMembers1 = await module.remove_role_member(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def account_role_upsert_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = AccountRoleUpsertRole1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  await module.upsert_role(
    data.name,
    data.mask,
    data.display,
    auth_ctx.role_mask,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def account_role_delete_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = AccountRoleDeleteRole1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  await module.delete_role(data.name, auth_ctx.role_mask)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
