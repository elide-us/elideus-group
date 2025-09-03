from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.role_admin_module import RoleAdminModule
from .models import (
  AccountRoleRoleItem1,
  AccountRoleList1,
  AccountRoleMemberUpdate1,
  AccountRoleMembers1,
  AccountRoleUserItem1,
  AccountRoleUpsertRole1,
  AccountRoleDeleteRole1,
)


async def account_role_get_roles_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  role_admin: RoleAdminModule = request.app.state.role_admin
  roles_raw = await role_admin.list_roles()
  roles = [AccountRoleRoleItem1(**r) for r in roles_raw]
  payload = AccountRoleList1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def account_role_get_role_members_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  role = payload.get("role")
  if not role:
    raise HTTPException(status_code=400, detail="Missing role")
  role_admin: RoleAdminModule = request.app.state.role_admin
  members_raw, non_raw = await role_admin.get_role_members(role)
  members = [AccountRoleUserItem1(**m) for m in members_raw]
  non_members = [AccountRoleUserItem1(**m) for m in non_raw]
  res = AccountRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def account_role_add_role_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  members_raw, non_raw = await role_admin.add_role_member(data.role, data.userGuid)
  members = [AccountRoleUserItem1(**m) for m in members_raw]
  non_members = [AccountRoleUserItem1(**m) for m in non_raw]
  res = AccountRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def account_role_remove_role_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  members_raw, non_raw = await role_admin.remove_role_member(data.role, data.userGuid)
  members = [AccountRoleUserItem1(**m) for m in members_raw]
  non_members = [AccountRoleUserItem1(**m) for m in non_raw]
  res = AccountRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def account_role_upsert_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountRoleUpsertRole1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  await role_admin.upsert_role(data.name, int(data.mask), data.display)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def account_role_delete_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountRoleDeleteRole1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  await role_admin.delete_role(data.name)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
