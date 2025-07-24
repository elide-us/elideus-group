from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.account.users.models import (
  AccountUsersList1,
  UserListItem,
  AccountUserRoles1,
  AccountUserRolesUpdate1,
  AccountUserCreditsUpdate1,
  AccountUserDisplayNameUpdate1,
  AccountUserProfile1,
)
from server.modules.database_module import DatabaseModule, _utos
from server.modules.storage_module import StorageModule
from server.helpers.roles import (
  mask_to_names,
  names_to_mask,
  ROLE_REGISTERED,
)

async def get_users_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.select_users()
  users = [UserListItem(guid=_utos(r['guid']), displayName=r['display_name']) for r in rows]
  payload = AccountUsersList1(users=users)
  return RPCResponse(op='urn:account:users:list:1', payload=payload, version=1)

async def get_user_roles_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: DatabaseModule = request.app.state.database
  mask = await db.get_user_roles(guid)
  roles = mask_to_names(mask)
  payload = AccountUserRoles1(roles=roles)
  return RPCResponse(op='urn:account:users:get_roles:1', payload=payload, version=1)

async def set_user_roles_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  data = AccountUserRolesUpdate1(**payload)
  db: DatabaseModule = request.app.state.database
  mask = names_to_mask(data.roles) | ROLE_REGISTERED
  await db.set_user_roles(data.userGuid, mask)
  payload = AccountUserRoles1(roles=mask_to_names(mask))
  return RPCResponse(op='urn:account:users:set_roles:1', payload=payload, version=1)

async def list_available_roles_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.list_roles()
  names = [r['name'] for r in rows]
  payload = AccountUserRoles1(roles=names)
  return RPCResponse(op='urn:account:users:list_roles:1', payload=payload, version=1)

async def get_user_profile_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  db: DatabaseModule = request.app.state.database
  storage: StorageModule = request.app.state.storage
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUserProfile1(
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
  return RPCResponse(op='urn:account:users:get_profile:1', payload=payload, version=1)

async def set_user_credits_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  data = AccountUserCreditsUpdate1(**payload)
  db: DatabaseModule = request.app.state.database
  storage: StorageModule = request.app.state.storage
  await db.set_user_credits(data.userGuid, data.credits)
  user = await db.get_user_profile(data.userGuid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUserProfile1(
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
  return RPCResponse(op='urn:account:users:set_credits:1', payload=payload, version=1)

async def set_user_display_name_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  data = AccountUserDisplayNameUpdate1(**payload)
  db: DatabaseModule = request.app.state.database
  storage: StorageModule = request.app.state.storage
  await db.update_display_name(data.userGuid, data.displayName)
  user = await db.get_user_profile(data.userGuid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUserProfile1(
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
  return RPCResponse(op='urn:account:users:set_display_name:1', payload=payload, version=1)

async def enable_user_storage_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  guid = payload.get('userGuid')
  if not guid:
    raise HTTPException(status_code=400, detail='Missing userGuid')
  storage: StorageModule = request.app.state.storage
  db: DatabaseModule = request.app.state.database
  await storage.ensure_user_folder(guid)
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUserProfile1(
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
  return RPCResponse(op='urn:account:users:enable_storage:1', payload=payload, version=1)
