from fastapi import HTTPException, Request

from rpc.account.users.models import (AccountUsersSetCredits1,
                                      AccountUsersSetDisplay1,
                                      AccountUsersGetProfile1)
from rpc.helpers import (ROLE_REGISTERED, get_rpcrequest_from_request)
from rpc.models import RPCRequest, RPCResponse
from server.modules.mssql_module import MSSQLModule, _utos
from server.modules.storage_module import StorageModule

async def account_users_get_profile_v1(request: Request) -> RPCResponse:
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
  payload = AccountUsersGetProfile1(
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
  )
  return RPCResponse(op='urn:account:users:get_profile:1', payload=payload, version=1)

async def account_users_set_credits_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  payload = rpc_request.payload or {}
  data = AccountUsersSetCredits1(**payload)
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  await db.set_user_credits(data.userGuid, data.credits)
  user = await db.get_user_profile(data.userGuid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUsersGetProfile1(
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
  )
  return RPCResponse(op='urn:account:users:set_credits:1', payload=payload, version=1)

async def account_users_set_display_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  payload = rpc_request.payload or {}
  data = AccountUsersSetDisplay1(**payload)
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  await db.update_display_name(data.userGuid, data.displayName)
  user = await db.get_user_profile(data.userGuid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = AccountUsersGetProfile1(
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
  )
  return RPCResponse(op='urn:account:users:set_display_name:1', payload=payload, version=1)

async def account_users_enable_storage_v1(request: Request) -> RPCResponse:
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
  payload = AccountUsersGetProfile1(
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
  )
  return RPCResponse(op='urn:account:users:enable_storage:1', payload=payload, version=1)

