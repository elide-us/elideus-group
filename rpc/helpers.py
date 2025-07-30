import logging
from fastapi import Request
from server.modules.auth_module import AuthModule
from server.modules.mssql_module import MSSQLModule
from rpc.models import RPCRequest

def _get_token_from_request(request: Request) -> str:
  header = request.headers.get('authorization')
  if not header or not header.lower().startswith('bearer '):
    logging.warning("No bearer token found in request headers")
  return header.split(' ', 1)[1].strip()

async def _process_rpcrequest(request: Request) -> RPCRequest:
  _auth: AuthModule = request.app.state.auth
  _mssql: MSSQLModule = request.app.state.mssql

  body = await request.json()
  rpc_request = RPCRequest(**body)

  token: str = _get_token_from_request(request)
  data: dict[str, str] = await _auth.decode_bearer_token(token)

  rpc_request.user_guid = data.get('guid')
  rpc_request.user_role = await _mssql.get_user_roles(rpc_request.user_guid)

  return rpc_request

async def get_rpcrequest_from_request(request):
  rpc_request = await _process_rpcrequest(request)
  parts = rpc_request.op.split(':')
  return rpc_request, parts

