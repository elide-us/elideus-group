from fastapi import HTTPException, Request

from rpc.helpers import unbox_request, bit_to_mask
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from .models import (
  ServiceRolesRoles1,
  ServiceRolesUpsertRole1,
  ServiceRolesDeleteRole1,
  ServiceRolesRoleMemberUpdate1,
  ServiceRolesRoleMembers1,
  ServiceRolesUserItem1,
)


async def service_roles_get_roles_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth
  payload = ServiceRolesRoles1(roles=list(auth.get_role_names(exclude_registered=True)))
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def service_roles_upsert_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesUpsertRole1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:upsert_role:1", {
    "name": data.name,
    "mask": bit_to_mask(data.bit),
    "display": data.display,
  })
  auth: AuthModule = request.app.state.auth
  await auth.refresh_role_cache()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def service_roles_delete_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesDeleteRole1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:delete_role:1", {"name": data.name})
  auth: AuthModule = request.app.state.auth
  await auth.refresh_role_cache()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def _fetch_role_members(db: DbModule, role: str) -> ServiceRolesRoleMembers1:
  mem_res = await db.run("db:security:roles:get_role_members:1", {"role": role})
  non_res = await db.run("db:security:roles:get_role_non_members:1", {"role": role})
  members = [
    ServiceRolesUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in mem_res.rows
  ]
  non_members = [
    ServiceRolesUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in non_res.rows
  ]
  return ServiceRolesRoleMembers1(members=members, nonMembers=non_members)


async def service_roles_get_role_members_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  role = payload.get("role")
  if not role:
    raise HTTPException(status_code=400, detail="Missing role")
  db: DbModule = request.app.state.db
  members = await _fetch_role_members(db, role)
  return RPCResponse(
    op=rpc_request.op,
    payload=members.model_dump(),
    version=rpc_request.version,
  )


async def service_roles_add_role_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:add_role_member:1", {
    "role": data.role,
    "user_guid": data.userGuid,
  })
  members = await _fetch_role_members(db, data.role)
  return RPCResponse(
    op=rpc_request.op,
    payload=members.model_dump(),
    version=rpc_request.version,
  )


async def service_roles_remove_role_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:remove_role_member:1", {
    "role": data.role,
    "user_guid": data.userGuid,
  })
  members = await _fetch_role_members(db, data.role)
  return RPCResponse(
    op=rpc_request.op,
    payload=members.model_dump(),
    version=rpc_request.version,
  )

