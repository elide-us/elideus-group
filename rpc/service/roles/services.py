from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.role_admin_module import RoleAdminModule
from .models import (
  ServiceRolesRoleItem1,
  ServiceRolesList1,
  ServiceRolesUpsertRole1,
  ServiceRolesDeleteRole1,
)


async def service_roles_get_roles_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  role_admin: RoleAdminModule = request.app.state.role_admin
  roles_raw = await role_admin.list_roles()
  roles = [ServiceRolesRoleItem1(**r) for r in roles_raw]
  payload = ServiceRolesList1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def service_roles_upsert_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesUpsertRole1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  await role_admin.upsert_role(data.name, int(data.mask), data.display)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def service_roles_delete_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesDeleteRole1(**(rpc_request.payload or {}))
  role_admin: RoleAdminModule = request.app.state.role_admin
  await role_admin.delete_role(data.name)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )
