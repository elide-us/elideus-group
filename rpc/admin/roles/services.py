from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  AdminRolesMembers1,
  AdminRolesRoleMemberUpdate1,
  AdminRolesUserItem1,
)


async def fetch_role_members(db: DbModule, role: str) -> AdminRolesMembers1:
  mem_res = await db.run("db:security:roles:get_role_members:1", {"role": role})
  non_res = await db.run("db:security:roles:get_role_non_members:1", {"role": role})
  members = [
    AdminRolesUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in mem_res.rows
  ]
  non_members = [
    AdminRolesUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in non_res.rows
  ]
  return AdminRolesMembers1(members=members, nonMembers=non_members)


async def admin_roles_get_members_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  role = payload.get("role")
  if not role:
    raise HTTPException(status_code=400, detail="Missing role")
  db: DbModule = request.app.state.db
  members = await fetch_role_members(db, role)
  return RPCResponse(
    op=rpc_request.op,
    payload=members.model_dump(),
    version=rpc_request.version,
  )


async def add_role_member(db: DbModule, role: str, user_guid: str) -> AdminRolesMembers1:
  await db.run(
    "db:security:roles:add_role_member:1",
    {"role": role, "user_guid": user_guid},
  )
  return await fetch_role_members(db, role)


async def admin_roles_add_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AdminRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  members = await add_role_member(db, data.role, data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=members.model_dump(),
    version=rpc_request.version,
  )


async def remove_role_member(db: DbModule, role: str, user_guid: str) -> AdminRolesMembers1:
  await db.run(
    "db:security:roles:remove_role_member:1",
    {"role": role, "user_guid": user_guid},
  )
  return await fetch_role_members(db, role)


async def admin_roles_remove_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AdminRolesRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  members = await remove_role_member(db, data.role, data.userGuid)
  return RPCResponse(
    op=rpc_request.op,
    payload=members.model_dump(),
    version=rpc_request.version,
  )

