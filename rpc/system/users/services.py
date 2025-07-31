from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.helpers import get_rpcrequest_from_request
from rpc.system.users.models import (
  SystemUsersList1,
  UserListItem,
  SystemUserRoles1,
  SystemUserRolesUpdate1,
  SystemUserCreditsUpdate1,
  SystemUserProfile1
)
from server.modules.mssql_module import MSSQLModule, _utos
from server.modules.storage_module import StorageModule
from rpc.helpers import (
  mask_to_names,
  names_to_mask,
  ROLE_REGISTERED,
)

async def get_users_v1(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.select_users()
  users = [UserListItem(guid=_utos(r['guid']), displayName=r['display_name']) for r in rows]
  payload = SystemUsersList1(users=users)
  return RPCResponse(op='urn:system:users:list:1', payload=payload, version=1)

async def get_user_roles_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: MSSQLModule = request.app.state.mssql
  mask = await db.get_user_roles(guid)
  roles = mask_to_names(mask)
  payload = SystemUserRoles1(roles=roles)
  return RPCResponse(op='urn:system:users:get_roles:1', payload=payload, version=1)

async def set_user_roles_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  payload = rpc_request.payload or {}
  data = SystemUserRolesUpdate1(**payload)
  db: MSSQLModule = request.app.state.mssql
  mask = names_to_mask(data.roles) | ROLE_REGISTERED
  await db.set_user_roles(data.userGuid, mask)
  payload = SystemUserRoles1(roles=mask_to_names(mask))
  return RPCResponse(op='urn:system:users:set_roles:1', payload=payload, version=1)

async def list_available_roles_v1(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_roles()
  names = [r['name'] for r in rows]
  payload = SystemUserRoles1(roles=names)
  return RPCResponse(op='urn:system:users:list_roles:1', payload=payload, version=1)

async def get_user_profile_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = SystemUserProfile1(
    guid=_utos(user.get('guid')),
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', ''),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=user.get('profile_image'),
    credits=user.get('credits', 0),
    storageUsed=await storage.get_user_folder_size(guid),
    storageEnabled=await storage.user_folder_exists(guid),
    displayEmail=user.get('display_email', False),
    rotationToken=_utos(user.get('rotation_token')) if user.get('rotation_token') else None,
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:system:users:get_profile:1', payload=payload, version=1)

async def set_user_credits_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  payload = rpc_request.payload or {}
  data = SystemUserCreditsUpdate1(**payload)
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  await db.set_user_credits(data.userGuid, data.credits)
  user = await db.get_user_profile(data.userGuid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = SystemUserProfile1(
    guid=_utos(user.get('guid')),
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', ''),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=user.get('profile_image'),
    credits=user.get('credits', data.credits),
    storageUsed=await storage.get_user_folder_size(data.userGuid),
    storageEnabled=await storage.user_folder_exists(data.userGuid),
    displayEmail=user.get('display_email', False),
    rotationToken=_utos(user.get('rotation_token')) if user.get('rotation_token') else None,
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:system:users:set_credits:1', payload=payload, version=1)

async def enable_user_storage_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)
  
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  storage: StorageModule = request.app.state.storage
  db: MSSQLModule = request.app.state.mssql
  await storage.ensure_user_folder(guid)
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = SystemUserProfile1(
    guid=_utos(user.get('guid')),
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', ''),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=user.get('profile_image'),
    credits=user.get('credits', 0),
    storageUsed=await storage.get_user_folder_size(guid),
    storageEnabled=await storage.user_folder_exists(guid),
    displayEmail=user.get('display_email', False),
    rotationToken=_utos(user.get('rotation_token')) if user.get('rotation_token') else None,
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:system:users:enable_storage:1', payload=payload, version=1)
