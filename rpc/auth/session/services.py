from fastapi import Request, HTTPException
from rpc.models import RPCResponse
from rpc.helpers import get_rpcrequest_from_request
from rpc.auth.session.models import AuthSessionTokens1
from server.modules.auth_module import AuthModule
from server.modules.mssql_module import MSSQLModule

async def refresh_v1(request: Request) -> RPCResponse:
  rpc_request = get_rpcrequest_from_request(request)
  
  payload = rpc_request.payload or {}
  rotation = payload.get('rotationToken')
  if not rotation:
    raise HTTPException(status_code=400, detail='Missing rotationToken')
  _auth: AuthModule = request.app.state.auth
  _mssql: MSSQLModule = request.app.state.mssql
  data = await _auth.decode_rotation_token(rotation)
  session = await _mssql.get_session_by_rotation(rotation)
  if not session:
    raise HTTPException(status_code=404, detail='Session not found')
  guid = data['guid']
  bearer = _auth.make_bearer_token(guid)
  new_rotation, exp = _auth.make_rotation_token(guid)
  await _mssql.update_session_tokens(session['session_id'], bearer, new_rotation, exp)
  payload = AuthSessionTokens1(bearerToken=bearer, rotationToken=new_rotation, rotationExpires=exp)
  return RPCResponse(op='urn:auth:session:refresh:1', payload=payload, version=1)

async def invalidate_v1(request: Request) -> RPCResponse:
  rpc_request = get_rpcrequest_from_request(request)

  payload = rpc_request.payload or {}
  rotation = payload.get('rotationToken')
  if not rotation:
    raise HTTPException(status_code=400, detail='Missing rotationToken')
  _mssql: MSSQLModule = request.app.state.mssql
  session = await _mssql.get_session_by_rotation(rotation)
  if session:
    await _mssql.delete_session(session['session_id'])
  return RPCResponse(op='urn:auth:session:invalidate:1', payload=True, version=1)
