from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.account.users.models import (
  UserListItem,
  AccountUsersList2,
  AccountUserRoles2,
  AccountUserRolesUpdate2,
  AccountUserCreditsUpdate2,
  AccountUserDisplayNameUpdate2,
  AccountUserProfile2,
)
from server.modules.mssql_module import MSSQLModule, _utos
from server.modules.storage_module import StorageModule
from server.helpers.roles import (
  mask_to_names,
  names_to_mask,
  ROLE_REGISTERED,
)

async def get_users_v2(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.select_users()
  users = [UserListItem(guid=_utos(r['guid']), displayName=r['display_name']) for r in rows]
  payload = AccountUsersList2(users=users)
  return RPCResponse(op='urn:account:users:list:2', payload=payload, version=2)

async def get_user_roles_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: MSSQLModule = request.app.state.mssql
  mask = await db.get_user_roles(guid)
  roles = mask_to_names(mask)
  payload = AccountUserRoles2(roles=roles)
  return RPCResponse(op='urn:account:users:get_roles:2', payload=payload, version=2)

async def set_user_roles_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  data = AccountUserRolesUpdate2(**payload)
  db: MSSQLModule = request.app.state.mssql
  mask = names_to_mask(data.roles) | ROLE_REGISTERED
  await db.set_user_roles(data.userGuid, mask)
  payload = AccountUserRoles2(roles=mask_to_names(mask))
  return RPCResponse(op='urn:account:users:set_roles:2', payload=payload, version=2)

async def list_available_roles_v2(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_roles()
  names = [r['name'] for r in rows]
  payload = AccountUserRoles2(roles=names)
  return RPCResponse(op='urn:account:users:list_roles:2', payload=payload, version=2)

async def get_user_profile_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUserProfile2(
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
  return RPCResponse(op='urn:account:users:get_profile:2', payload=payload, version=2)

async def set_user_credits_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  data = AccountUserCreditsUpdate2(**payload)
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  await db.set_user_credits(data.userGuid, data.credits)
  user = await db.get_user_profile(data.userGuid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUserProfile2(
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
  return RPCResponse(op='urn:account:users:set_credits:2', payload=payload, version=2)

async def set_user_display_name_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  data = AccountUserDisplayNameUpdate2(**payload)
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  await db.update_display_name(data.userGuid, data.displayName)
  user = await db.get_user_profile(data.userGuid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUserProfile2(
    guid=_utos(user.get('guid')),
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', data.displayName),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=user.get('profile_image'),
    credits=user.get('credits', 0),
    storageUsed=await storage.get_user_folder_size(data.userGuid),
    storageEnabled=await storage.user_folder_exists(data.userGuid),
    displayEmail=user.get('display_email', False),
    rotationToken=_utos(user.get('rotation_token')) if user.get('rotation_token') else None,
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:account:users:set_display_name:2', payload=payload, version=2)

async def enable_user_storage_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
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
  payload = AccountUserProfile2(
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
  return RPCResponse(op='urn:account:users:enable_storage:2', payload=payload, version=2)
