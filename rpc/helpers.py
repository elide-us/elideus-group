from __future__ import annotations
import logging, uuid

from typing import TYPE_CHECKING
from fastapi import HTTPException, Request

from server.models import RPCRequest
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

def _get_discord_id_from_request(request: Request) -> str | None:
  return request.headers.get('x-discord-id')

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
    logging.debug("[RPC] Resolved roles for %s: %s (mask=%#018x)", auth_ctx.user_guid, roles, mask)
  else:
    if domain == 'discord':
      discord_id = _get_discord_id_from_request(request)
      if not discord_id:
        raise HTTPException(status_code=401, detail='Missing or invalid authorization header')
      _auth: AuthModule = request.app.state.auth
      guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"discord:{discord_id}"))
      auth_ctx.user_guid = guid
      roles, mask = await _auth.get_user_roles(guid)
      auth_ctx.roles = roles
      auth_ctx.role_mask = mask
      rpc_request.user_guid = guid
      rpc_request.roles = roles
      rpc_request.role_mask = mask
      if not (mask & _auth.role_registered):
        raise HTTPException(status_code=403, detail='Forbidden')
      logging.debug("[RPC] Resolved roles for %s: %s (mask=%#018x)", guid, roles, mask)
    elif domain not in ('public', 'auth'):
      raise HTTPException(status_code=401, detail='Missing or invalid authorization header')

  return rpc_request, auth_ctx

async def unbox_request(request):
  if getattr(request.state, 'rpc_request', None) and getattr(request.state, 'auth_ctx', None):
    rpc_request = request.state.rpc_request
    auth_ctx = request.state.auth_ctx
  else:
    rpc_request, auth_ctx = await _process_rpcrequest(request)
    request.state.rpc_request = rpc_request
    request.state.auth_ctx = auth_ctx
  parts = rpc_request.op.split(':')
  return rpc_request, auth_ctx, parts
