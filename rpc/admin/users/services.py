from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.admin.users.models import (
  AdminUsersList1,
  UserListItem,
  AdminUserRoles1,
  AdminUserRolesUpdate1,
  AdminUserProfile1,
)
from server.modules.database_module import DatabaseModule, _utos
from server.helpers.roles import mask_to_names, names_to_mask, ROLE_NAMES

async def get_users_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.select_users()
  users = [UserListItem(guid=_utos(r['guid']), displayName=r['display_name']) for r in rows]
  payload = AdminUsersList1(users=users)
  return RPCResponse(op='urn:admin:users:list:1', payload=payload, version=1)

async def get_user_roles_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: DatabaseModule = request.app.state.database
  mask = await db.get_user_roles(guid)
  roles = mask_to_names(mask)
  payload = AdminUserRoles1(roles=roles)
  return RPCResponse(op='urn:admin:users:get_roles:1', payload=payload, version=1)

async def set_user_roles_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  data = AdminUserRolesUpdate1(**payload)
  db: DatabaseModule = request.app.state.database
  mask = names_to_mask(data.roles)
  await db.set_user_roles(data.userGuid, mask)
  payload = AdminUserRoles1(roles=data.roles)
  return RPCResponse(op='urn:admin:users:set_roles:1', payload=payload, version=1)

async def list_available_roles_v1(request: Request) -> RPCResponse:
  payload = AdminUserRoles1(roles=ROLE_NAMES)
  return RPCResponse(op='urn:admin:users:list_roles:1', payload=payload, version=1)

async def get_user_profile_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: DatabaseModule = request.app.state.database
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AdminUserProfile1(
    guid=_utos(user.get('guid')),
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', ''),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=None,
    credits=user.get('credits', 0),
    storageUsed=user.get('storage_used', 0),
    displayEmail=user.get('display_email', False),
    rotationToken=_utos(user.get('rotation_token')) if user.get('rotation_token') else None,
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:admin:users:get_profile:1', payload=payload, version=1)
