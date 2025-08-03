from fastapi import HTTPException, Request

from rpc.account.roles.models import (AccountRolesMemberList1,
                                      AccountRolesMember1)
from rpc.account.users.models import UserListItem
from rpc.helpers import get_rpcrequest_from_request, mask_to_bit, bit_to_mask
from rpc.models import RPCRequest, RPCResponse
from server.helpers import roles as role_helper
from server.modules.mssql_module import MSSQLModule, _utos


async def account_roles_get_members_v1(rpc_request, request: Request) -> RPCResponse:
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
  payload = AccountRolesMemberList1(members=members, nonMembers=non_members)
  return RPCResponse(op='urn:account:roles:get_members:1', payload=payload, version=1)

async def account_roles_add_member_v1(rpc_request, request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = AccountRolesMember1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_roles()
  role_map = {r['name']: int(r['mask']) for r in rows}
  mask = role_map.get(data.role)
  if mask is None:
    raise HTTPException(status_code=404, detail='Role not found')
  current = await db.get_user_roles(data.userGuid)
  await db.set_user_roles(data.userGuid, current | mask | role_helper.ROLE_REGISTERED)
  new_req = RPCRequest(op='', payload={'role': data.role}, version=1)
  return await account_roles_get_members_v1(new_req, request)

async def account_roles_remove_member_v1(rpc_request, request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = AccountRolesMember1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_roles()
  role_map = {r['name']: int(r['mask']) for r in rows}
  mask = role_map.get(data.role)
  if mask is None:
    raise HTTPException(status_code=404, detail='Role not found')
  current = await db.get_user_roles(data.userGuid)
  await db.set_user_roles(data.userGuid, current & ~mask | role_helper.ROLE_REGISTERED)
  new_req = RPCRequest(op='', payload={'role': data.role}, version=1)
  return await account_roles_get_members_v1(new_req, request)

