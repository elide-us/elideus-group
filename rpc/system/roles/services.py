import logging
from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.role_admin_module import RoleAdminModule
from .models import (
  SystemRolesList1,
  SystemRolesRoleItem1,
  SystemRolesUpsertRole1,
  SystemRolesDeleteRole1,
)


async def system_roles_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[system_roles_get_roles_v1] user=%s roles=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  role_admin: RoleAdminModule = request.app.state.role_admin
  roles_raw = await role_admin.list_roles()
  roles = [SystemRolesRoleItem1(**r) for r in roles_raw]
  payload = SystemRolesList1(roles=roles)
  logging.debug(
    "[system_roles_get_roles_v1] returning %d roles",
    len(roles),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def system_roles_upsert_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[system_roles_upsert_role_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  data = SystemRolesUpsertRole1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  await role_admin.upsert_role(data.name, int(data.mask), data.display)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def system_roles_delete_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[system_roles_delete_role_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  data = SystemRolesDeleteRole1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  await role_admin.delete_role(data.name)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
