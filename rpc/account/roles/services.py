from fastapi import Request, HTTPException
from rpc.account.roles.models import (
  RoleItem,
  AccountRolesList1,
  AccountRoleUpdate1,
  AccountRoleDelete1,
  AccountRoleMembers1,
  AccountRoleMemberUpdate1,
)
from rpc.account.users.models import UserListItem
from rpc.models import RPCRequest, RPCResponse
from server.modules.database_module import DatabaseModule, _utos
from server.helpers import roles as role_helper


def mask_to_bit(mask: int) -> int:
  if mask == 0:
    return 0
  return (mask.bit_length() - 1)

def bit_to_mask(bit: int) -> int:
  if bit < 0 or bit >= 63:
    raise HTTPException(status_code=400, detail='Invalid bit index')
  return 1 << bit

async def list_roles_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.list_roles()
  roles = [
    RoleItem(name=r['name'], display=r['display'], bit=mask_to_bit(int(r['mask'])))
    for r in rows
  ]
  roles.sort(key=lambda r: r.bit)
  payload = AccountRolesList1(roles=roles)
  return RPCResponse(op='urn:account:roles:list:1', payload=payload, version=1)

async def set_role_v1(rpc_request, request: Request) -> RPCResponse:
  data = AccountRoleUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  mask = bit_to_mask(data.bit)
  await db.set_role(data.name, mask, data.display)
  await role_helper.load_roles(db)
  return await list_roles_v1(request)

async def delete_role_v1(rpc_request, request: Request) -> RPCResponse:
  data = AccountRoleDelete1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.delete_role(data.name)
  await role_helper.load_roles(db)
  return await list_roles_v1(request)

async def get_role_members_v1(rpc_request, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  role = payload.get('role')
  if not role:
    raise HTTPException(status_code=400, detail='Missing role')
  db: DatabaseModule = request.app.state.database
  rows = await db.list_roles()
  role_map = {r['name']: int(r['mask']) for r in rows}
  mask = role_map.get(role)
  if mask is None:
    raise HTTPException(status_code=404, detail='Role not found')
  members = [
    UserListItem(guid=_utos(r['guid']), displayName=r['display_name'])
    for r in await db.select_users_with_role(mask)
  ]
  non_members = [
    UserListItem(guid=_utos(r['guid']), displayName=r['display_name'])
    for r in await db.select_users_without_role(mask)
  ]
  payload = AccountRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(op='urn:account:roles:get_members:1', payload=payload, version=1)

async def add_role_member_v1(rpc_request, request: Request) -> RPCResponse:
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  rows = await db.list_roles()
  role_map = {r['name']: int(r['mask']) for r in rows}
  mask = role_map.get(data.role)
  if mask is None:
    raise HTTPException(status_code=404, detail='Role not found')
  current = await db.get_user_roles(data.userGuid)
  await db.set_user_roles(data.userGuid, current | mask | role_helper.ROLE_REGISTERED)
  new_req = RPCRequest(op='', payload={'role': data.role}, version=1)
  return await get_role_members_v1(new_req, request)

async def remove_role_member_v1(rpc_request, request: Request) -> RPCResponse:
  data = AccountRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  rows = await db.list_roles()
  role_map = {r['name']: int(r['mask']) for r in rows}
  mask = role_map.get(data.role)
  if mask is None:
    raise HTTPException(status_code=404, detail='Role not found')
  current = await db.get_user_roles(data.userGuid)
  await db.set_user_roles(data.userGuid, current & ~mask | role_helper.ROLE_REGISTERED)
  new_req = RPCRequest(op='', payload={'role': data.role}, version=1)
  return await get_role_members_v1(new_req, request)
