import logging

from fastapi import HTTPException, Request

from rpc.models import RPCRequest
from server.modules.auth_module import AuthModule
from server.modules.mssql_module import MSSQLModule


def mask_to_bit(mask: int) -> int:
  if mask == 0:
    return 0
  return (mask.bit_length() - 1)

def bit_to_mask(bit: int) -> int:
  if bit < 0 or bit >= 63:
    raise HTTPException(status_code=400, detail='Invalid bit index')
  return 1 << bit

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
  data: dict[str, str] = await _auth.decode_bearer_token(token) #TODO: Include user_role int in bearer token

  rpc_request.user_guid = data.get('guid')
  rpc_request.user_role = await _mssql.get_user_roles(rpc_request.user_guid)

  return rpc_request

async def get_rpcrequest_from_request(request):
  rpc_request = await _process_rpcrequest(request)
  parts = rpc_request.op.split(':')
  return rpc_request, parts

# Mapping of role names to their masks loaded from the database.
ROLES: dict[str, int] = {}

# List of all roles except ``ROLE_REGISTERED`` for convenience.
ROLE_NAMES: list[str] = []

# ``ROLE_REGISTERED`` is used frequently so expose it directly.  It will be
# updated when ``load_roles`` is called.  Default to ``1`` so code using the
# constant before roles are loaded behaves as expected.
ROLE_REGISTERED: int = 1

import pyodbc


async def load_roles(db) -> None:
  try:
    rows = await db.list_roles()
  except pyodbc.Error:
    return
  if not rows:
    return
  ROLES.clear()
  for r in rows:
    ROLES[r['name']] = int(r['mask'])
  global ROLE_NAMES, ROLE_REGISTERED
  ROLE_NAMES = [n for n in ROLES.keys() if n != 'ROLE_REGISTERED']
  ROLE_REGISTERED = ROLES.get('ROLE_REGISTERED', 0)


################################################################################
## We probably only need to keep the two functions below here
## and they can probably be moved to auth module...
################################################################################

def mask_to_names(mask: int) -> list[str]:
  return [name for name, bit in ROLES.items() if mask & bit]

def names_to_mask(names: list[str]) -> int:
  mask = 0
  for name in names:
    mask |= ROLES.get(name, 0)
  return mask
