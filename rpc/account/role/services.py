from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.role_admin_module import RoleAdminModule
from .models import (
  AccountRoleAggregateItem1,
  AccountRoleAggregateList1,
  AccountRoleRoleItem1,
  AccountRoleList1,
  AccountRoleGetMembersRequest1,
  AccountRoleMemberUpdate1,
  AccountRoleMembers1,
  AccountRoleUserItem1,
  AccountRoleUpsertRole1,
  AccountRoleDeleteRole1,
)


async def account_role_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: RoleAdminModule = request.app.state.role_admin
  roles_raw = await module.list_roles(auth_ctx.role_mask)
  roles = [AccountRoleRoleItem1(**r) for r in roles_raw]
  payload = AccountRoleList1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def account_role_get_all_role_members_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: RoleAdminModule = request.app.state.role_admin
  roles_raw = await module.get_all_role_members(auth_ctx.role_mask)
  roles = [AccountRoleAggregateItem1(**r) for r in roles_raw]
  payload = AccountRoleAggregateList1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def account_role_get_role_members_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  input_payload = AccountRoleGetMembersRequest1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  members_raw, non_raw = await module.get_role_members(input_payload.role)
  members = [AccountRoleUserItem1(**m) for m in members_raw]
  non_members = [AccountRoleUserItem1(**m) for m in non_raw]
  res = AccountRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def account_role_add_role_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  members_raw, non_raw = await module.add_role_member(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  members = [AccountRoleUserItem1(**m) for m in members_raw]
  non_members = [AccountRoleUserItem1(**m) for m in non_raw]
  res = AccountRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def account_role_remove_role_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  members_raw, non_raw = await module.remove_role_member(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  members = [AccountRoleUserItem1(**m) for m in members_raw]
  non_members = [AccountRoleUserItem1(**m) for m in non_raw]
  res = AccountRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def account_role_upsert_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = AccountRoleUpsertRole1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.upsert_role(
    data.name,
    int(data.mask),
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
  await module.delete_role(data.name, auth_ctx.role_mask)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
