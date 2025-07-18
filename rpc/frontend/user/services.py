from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.frontend.user.models import FrontendUserProfileData1
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
  profile = FrontendUserProfileData1(
    bearerToken=token,
    defaultProvider=user.get('provider_name', 'microsoft'),
    username=user.get('display_name', ''),
    email=user.get('email', ''),
    backupEmail=None,
    profilePicture=None,
    credits=user.get('credits', 0),
    displayEmail=user.get('display_email', False),
    rotationToken=user.get('rotation_token'),
    rotationExpires=user.get('rotation_expires'),
  )
  return RPCResponse(op='urn:frontend:user:profile_data:1', payload=profile, version=1)
