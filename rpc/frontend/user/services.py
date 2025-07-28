from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.frontend.user.models import FrontendUserProfileData1, FrontendUserSetDisplayName1
from server.modules.auth_module import AuthModule
from server.modules.mssql_module import MSSQLModule, _utos
from server.helpers.roles import mask_to_names
from server.modules.storage_module import StorageModule

async def get_profile_data_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  token = payload.get('bearerToken')
  if not token:
    raise HTTPException(status_code=401, detail='Missing bearer token')
  auth: AuthModule = request.app.state.auth
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  token_data = await auth.decode_bearer_token(token)
  guid = token_data['guid']
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  mask = await db.get_user_roles(guid)
  roles = mask_to_names(mask)
  payload = FrontendUserProfileData1(
    bearerToken=token,
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', ''),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=user.get('profile_image'),
    credits=user.get('credits', 0),
    storageUsed=await storage.get_user_folder_size(guid),
    storageEnabled=await storage.user_folder_exists(guid),
    displayEmail=user.get('display_email', False),
    roles=roles,
    rotationToken=_utos(user.get('rotation_token')) if user.get('rotation_token') else None,
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:frontend:user:profile_data:1', payload=payload, version=1)

async def set_display_name_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  token = payload.get('bearerToken')
  display_name = payload.get('displayName')
  if not token or display_name is None:
    raise HTTPException(status_code=400, detail='Missing parameters')
  auth: AuthModule = request.app.state.auth
  db: MSSQLModule = request.app.state.mssql
  storage: StorageModule = request.app.state.storage
  token_data = await auth.decode_bearer_token(token)
  guid = token_data['guid']
  await db.update_display_name(guid, display_name)
  user = await db.get_user_profile(guid)
  mask = await db.get_user_roles(guid)
  roles = mask_to_names(mask)
  payload = FrontendUserProfileData1(
    bearerToken=token,
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', display_name),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=user.get('profile_image'),
    credits=user.get('credits', 0),
    storageUsed=await storage.get_user_folder_size(guid),
    storageEnabled=await storage.user_folder_exists(guid),
    displayEmail=user.get('display_email', False),
    roles=roles,
    rotationToken=_utos(user.get('rotation_token')) if user.get('rotation_token') else None,
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:frontend:user:set_display_name:1', payload=payload, version=1)
