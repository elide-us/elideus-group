from __future__ import annotations
import logging

from typing import TYPE_CHECKING
from fastapi import HTTPException, Request

from rpc.models import RPCRequest
from server.models import AuthContext

if TYPE_CHECKING:
  from server.modules.auth_module import AuthModule
  from server.modules.db_module import DbModule


def mask_to_bit(mask: int) -> int:
  if mask == 0:
    return 0
  return (mask.bit_length() - 1)

def bit_to_mask(bit: int) -> int:
  if bit < 0 or bit >= 63:
    raise HTTPException(status_code=400, detail='Invalid bit index')
  return 1 << bit

def _get_token_from_request(request: Request) -> str | None:
  header = request.headers.get('authorization')
  if not header or not header.lower().startswith('bearer '):
    logging.debug("No bearer token found in request headers")
    return None
  return header.split(' ', 1)[1].strip()

async def _process_rpcrequest(request: Request) -> tuple[RPCRequest, AuthContext]:
  body = await request.json()
  rpc_request = RPCRequest(**body)

  token = _get_token_from_request(request)
  parts = rpc_request.op.split(':')
  domain = parts[1] if len(parts) > 1 else ''

  auth_ctx = AuthContext()

  if token:
    _auth: AuthModule = request.app.state.auth
    data: dict = await _auth.decode_session_token(token)
    auth_ctx.user_guid = data.get('sub')
    auth_ctx.provider = data.get('provider')
    auth_ctx.claims = data
    roles, mask = await _auth.get_user_roles(auth_ctx.user_guid)
    auth_ctx.roles = roles
    auth_ctx.role_mask = mask
    rpc_request.user_guid = auth_ctx.user_guid
    rpc_request.roles = roles
    rpc_request.role_mask = mask
  else:
    if domain not in ('public', 'auth'):
      raise HTTPException(status_code=401, detail='Missing or invalid authorization header')

  return rpc_request, auth_ctx

async def get_rpcrequest_from_request(request):
  if getattr(request.state, 'rpc_request', None) and getattr(request.state, 'auth_ctx', None):
    rpc_request = request.state.rpc_request
    auth_ctx = request.state.auth_ctx
  else:
    rpc_request, auth_ctx = await _process_rpcrequest(request)
    request.state.rpc_request = rpc_request
    request.state.auth_ctx = auth_ctx
  parts = rpc_request.op.split(':')
  return rpc_request, auth_ctx, parts
