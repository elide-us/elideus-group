from fastapi import HTTPException, Request

from rpc.models import RPCRequest, RPCResponse
from rpc.helpers import ROLE_REGISTERED, get_rpcrequest_from_request
from rpc.system.roles.models import (SystemRoleMembers1,
                                     SystemRoleMemberUpdate1,
                                     RoleMemberListItem1)
from server.modules.mssql_module import MSSQLModule, _utos


# TODO: RoleHelper stuff in this area

async def system_roles_get_members_v1(request: Request) -> RPCResponse:
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
    RoleMemberListItem1(guid=_utos(r['guid']), displayName=r['display_name'])
    for r in await db.select_users_with_role(mask)
  ]
  non_members = [
    RoleMemberListItem1(guid=_utos(r['guid']), displayName=r['display_name'])
    for r in await db.select_users_without_role(mask)
  ]
  payload = SystemRoleMembers1(members=members, nonMembers=non_members)
  return RPCResponse(op='urn:system:roles:get_members:1', payload=payload, version=1)

async def system_roles_add_member_v1(request: Request) -> RPCResponse:
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
  return await system_roles_get_members_v1(new_req, request)

async def system_roles_remove_member_v1(request: Request) -> RPCResponse:
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
  return await system_roles_get_members_v1(new_req, request)
