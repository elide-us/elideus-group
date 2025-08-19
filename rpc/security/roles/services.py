from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request, bit_to_mask
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from .models import (
  SecurityRolesRoles1,
  SecurityRolesUpsertRole1,
  SecurityRolesDeleteRole1,
  SecurityRolesRoleMemberUpdate1,
  SecurityRolesRoleMembers1,
  SecurityRolesUserItem1,
)


async def security_roles_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if (
    "ROLE_SECURITY_ADMIN" not in auth_ctx.roles
    and "ROLE_SYSTEM_ADMIN" not in auth_ctx.roles
  ):
    raise HTTPException(status_code=403, detail="Forbidden")
  auth: AuthModule = request.app.state.auth
  payload = SecurityRolesRoles1(roles=list(auth.get_role_names(exclude_registered=True)))
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def security_roles_upsert_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SECURITY_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = SecurityRolesUpsertRole1(**(rpc_request.payload or {}))
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


async def security_roles_delete_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SECURITY_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = SecurityRolesDeleteRole1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:delete_role:1", {"name": data.name})
  auth: AuthModule = request.app.state.auth
  await auth.refresh_role_cache()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def _fetch_role_members(db: DbModule, role: str) -> SecurityRolesRoleMembers1:
  mem_res = await db.run("db:security:roles:get_role_members:1", {"role": role})
  non_res = await db.run("db:security:roles:get_role_non_members:1", {"role": role})
  members = [
    SecurityRolesUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in mem_res.rows
  ]
  non_members = [
    SecurityRolesUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in non_res.rows
  ]
  return SecurityRolesRoleMembers1(members=members, nonMembers=non_members)


async def security_roles_get_role_members_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SECURITY_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
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


async def security_roles_add_role_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SECURITY_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = SecurityRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
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


async def security_roles_remove_role_member_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SECURITY_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = SecurityRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
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

