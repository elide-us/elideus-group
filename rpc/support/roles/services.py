from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.role_admin_module import RoleAdminModule
from .models import (
  SupportRolesMembers1,
  SupportRolesRoleMemberUpdate1,
  SupportRolesUserItem1,
)


async def support_roles_get_members_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  role = payload.get("role")
  if not role:
    raise HTTPException(status_code=400, detail="Missing role")
  module: RoleAdminModule = request.app.state.module
  members_raw, non_raw = await module.get_role_members(role)
  members = [SupportRolesUserItem1(**m) for m in members_raw]
  non_members = [SupportRolesUserItem1(**m) for m in non_raw]
  res = SupportRolesMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def support_roles_add_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = SupportRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.module
  members_raw, non_raw = await module.add_role_member(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  members = [SupportRolesUserItem1(**m) for m in members_raw]
  non_members = [SupportRolesUserItem1(**m) for m in non_raw]
  res = SupportRolesMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )


async def support_roles_remove_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = SupportRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.module
  members_raw, non_raw = await module.remove_role_member(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  members = [SupportRolesUserItem1(**m) for m in members_raw]
  non_members = [SupportRolesUserItem1(**m) for m in non_raw]
  res = SupportRolesMembers1(members=members, nonMembers=non_members)
  return RPCResponse(
    op=rpc_request.op,
    payload=res.model_dump(),
    version=rpc_request.version,
  )
