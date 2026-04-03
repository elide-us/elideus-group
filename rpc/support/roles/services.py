from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from .models import (
  SupportRolesGetMembersRequest1,
  SupportRolesMembers1,
  SupportRolesRoleMemberUpdate1,
)

if TYPE_CHECKING:
  from server.modules.role_admin_module import RoleAdminModule


async def support_roles_get_members_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  input_payload = SupportRolesGetMembersRequest1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: SupportRolesMembers1 = await module.get_role_members_for_support(input_payload.role)
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def support_roles_add_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = SupportRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: SupportRolesMembers1 = await module.add_role_member_for_support(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def support_roles_remove_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = SupportRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  module: RoleAdminModule = request.app.state.role_admin
  await module.on_ready()

  result: SupportRolesMembers1 = await module.remove_role_member_for_support(
    data.role,
    data.userGuid,
    auth_ctx.role_mask,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )
