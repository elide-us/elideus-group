from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  AccountRoleRoleItem1,
  AccountRoleList1,
  AccountRoleMemberUpdate1,
  AccountRoleMembers1,
  AccountRoleUserItem1,
)


async def account_role_get_roles_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  res = await db.run("db:system:roles:list:1", {})
  roles = [
    AccountRoleRoleItem1(
      name=r.get("name", ""),
      mask=str(r.get("mask", "")),
      display=r.get("display"),
    )
    for r in res.rows
    if r.get("name") != "ROLE_REGISTERED"
  ]
  payload = AccountRoleList1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def _fetch_role_members(db: DbModule, role: str) -> AccountRoleMembers1:
  mem_res = await db.run("db:security:roles:get_role_members:1", {"role": role})
  non_res = await db.run("db:security:roles:get_role_non_members:1", {"role": role})
  members = [
    AccountRoleUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in mem_res.rows
  ]
  non_members = [
    AccountRoleUserItem1(
      guid=r.get("guid", ""),
      displayName=r.get("display_name", ""),
    )
    for r in non_res.rows
  ]
  return AccountRoleMembers1(members=members, nonMembers=non_members)


async def account_role_get_role_members_v1(request: Request):
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


async def account_role_add_role_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
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


async def account_role_remove_role_member_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
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
