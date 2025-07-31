from fastapi import Request, HTTPException
from rpc.system.roles.models import (
  RoleItem,
  SystemRolesList1,
  SystemRoleUpdate1,
  SystemRoleDelete1,
  SystemRoleMembers1,
  SystemRoleMemberUpdate1
)
from rpc.system.users.models import UserListItem
from rpc.models import RPCRequest, RPCResponse
from server.modules.mssql_module import MSSQLModule, _utos
from rpc.helpers import get_rpcrequest_from_request
from rpc.helpers import ROLE_REGISTERED, load_roles


def mask_to_bit(mask: int) -> int:
  if mask == 0:
    return 0
  return (mask.bit_length() - 1)

def bit_to_mask(bit: int) -> int:
  if bit < 0 or bit >= 63:
    raise HTTPException(status_code=400, detail='Invalid bit index')
  return 1 << bit

# TODO: RoleHelper stuff in this area

async def get_role_members_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)
  
  payload = rpc_request.payload or {}
  role = payload.get('role')
  if not role:
    raise HTTPException(status_code=400, detail='Missing role')
  db: MSSQLModule = request.app.state.mssql
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
  payload = SystemRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(op='urn:system:roles:get_members:1', payload=payload, version=1)

async def list_roles_v1(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_roles()
  roles = [
    RoleItem(name=r['name'], display=r['display'], bit=mask_to_bit(int(r['mask'])))
    for r in rows
  ]
  roles.sort(key=lambda r: r.bit)
  payload = SystemRolesList1(roles=roles)
  return RPCResponse(op='urn:system:roles:list:1', payload=payload, version=1)

async def set_role_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = SystemRoleUpdate1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  mask = bit_to_mask(data.bit)
  await db.set_role(data.name, mask, data.display)
  await load_roles(db)
  return await list_roles_v1(request)

async def delete_role_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = SystemRoleDelete1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.delete_role(data.name)
  await load_roles(db)
  return await list_roles_v1(request)

async def add_role_member_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)
  
  data = SystemRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_roles()
  role_map = {r['name']: int(r['mask']) for r in rows}
  mask = role_map.get(data.role)
  if mask is None:
    raise HTTPException(status_code=404, detail='Role not found')
  current = await db.get_user_roles(data.userGuid)
  await db.set_user_roles(data.userGuid, current | mask | ROLE_REGISTERED)
  new_req = RPCRequest(op='', payload={'role': data.role}, version=1)
  return await get_role_members_v1(new_req, request)

async def remove_role_member_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)
  
  data = SystemRoleMemberUpdate1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_roles()
  role_map = {r['name']: int(r['mask']) for r in rows}
  mask = role_map.get(data.role)
  if mask is None:
    raise HTTPException(status_code=404, detail='Role not found')
  current = await db.get_user_roles(data.userGuid)
  await db.set_user_roles(data.userGuid, current & ~mask | ROLE_REGISTERED)
  new_req = RPCRequest(op='', payload={'role': data.role}, version=1)
  return await get_role_members_v1(new_req, request)
