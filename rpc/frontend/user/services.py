from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.frontend.user.models import FrontendUserProfileData1, FrontendUserSetDisplayName1
from server.modules.auth_module import AuthModule
from server.modules.database_module import DatabaseModule

async def get_profile_data_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  token = payload.get('bearerToken')
  if not token:
    raise HTTPException(status_code=401, detail='Missing bearer token')
  auth: AuthModule = request.app.state.auth
  db: DatabaseModule = request.app.state.database
  token_data = await auth.decode_bearer_token(token)
  guid = token_data['guid']
  user = await db.get_user_profile(guid)
  if not user:
    raise HTTPException(status_code=404, detail='User not found')
  payload = FrontendUserProfileData1(
    bearerToken=token,
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', ''),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=None,
    credits=user.get('credits', 0),
    storageUsed=user.get('storage_used', 0),
    displayEmail=user.get('display_email', False),
    rotationToken=user.get('rotation_token'),
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
  db: DatabaseModule = request.app.state.database
  token_data = await auth.decode_bearer_token(token)
  guid = token_data['guid']
  await db.update_display_name(guid, display_name)
  user = await db.get_user_profile(guid)
  payload = FrontendUserProfileData1(
    bearerToken=token,
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', display_name),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=None,
    credits=user.get('credits', 0),
    storageUsed=user.get('storage_used', 0),
    displayEmail=user.get('display_email', False),
    rotationToken=user.get('rotation_token'),
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:frontend:user:set_display_name:1', payload=payload, version=1)
