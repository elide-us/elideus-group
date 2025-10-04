from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

from server.models import AuthContext
from server.models import RPCRequest

if TYPE_CHECKING:
  from server.modules import AuthService


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

_logger = logging.getLogger(__name__)
_audit_logger = logging.getLogger('security.audit')


def _get_discord_id_from_request(request: Request) -> str | None:
  ctx = getattr(request.state, 'discord_ctx', None)
  if ctx and getattr(ctx, 'author', None):
    return str(getattr(ctx.author, 'id', ''))
  header_id = request.headers.get('x-discord-id') or request.headers.get('x-discord-user-id')
  if header_id:
    return str(header_id)
  return None


def _get_mtls_subject(request: Request) -> str | None:
  subject = getattr(request.state, 'mtls_subject_guid', None)
  if subject:
    return str(subject)
  header_subject = request.headers.get('x-mtls-subject-guid')
  if header_subject:
    return str(header_subject)
  return None


def resolve_required_mask(auth: 'AuthService', role_name: str) -> int:
  if not role_name:
    raise HTTPException(status_code=500, detail='Role name must be provided')
  try:
    return auth.require_role_mask(role_name)
  except KeyError as exc:
    message = f'Required role is undefined: {role_name}'
    _logger.error('[RPC] %s', message)
    raise HTTPException(status_code=500, detail=message) from exc


async def _validate_rpc_identity(
  request: Request,
  rpc_request: RPCRequest,
  parts: list[str],
) -> AuthContext:
  auth_ctx = AuthContext()
  token = _get_token_from_request(request)
  mtls_subject = _get_mtls_subject(request)
  domain = parts[1] if len(parts) > 1 else ''

  auth: AuthModule | None = getattr(request.app.state, 'auth', None)
  if not auth:
    if domain in ('public', 'auth'):
      return auth_ctx
    raise HTTPException(status_code=500, detail='Authentication module is unavailable')

  identity_source = None
  discord_id: str | None = None

  if domain in ('discord', 'webhook') and not (token or mtls_subject):
    raise HTTPException(status_code=401, detail='Signed token or MTLS assertion required')

  if token:
    try:
      data: dict = await auth.decode_session_token(token)
    except HTTPException:
      raise
    except Exception as exc:
      _logger.exception('[RPC] Failed to decode session token')
      raise HTTPException(status_code=401, detail='Invalid authorization token') from exc
    user_guid = data.get('sub')
    if not user_guid:
      raise HTTPException(status_code=401, detail='Invalid authorization token payload')
    roles, mask = await auth.get_user_roles(user_guid)
    auth_ctx.user_guid = user_guid
    auth_ctx.provider = data.get('provider')
    auth_ctx.claims = data
    auth_ctx.roles = roles
    auth_ctx.role_mask = mask
    rpc_request.user_guid = user_guid
    rpc_request.roles = roles
    rpc_request.role_mask = mask
    identity_source = 'token'
    _logger.debug('[RPC] Resolved roles for %s: %s (mask=%#018x)', user_guid, roles, mask)

  if not token and mtls_subject:
    roles, mask = await auth.get_user_roles(mtls_subject)
    auth_ctx.user_guid = mtls_subject
    auth_ctx.roles = roles
    auth_ctx.role_mask = mask
    rpc_request.user_guid = mtls_subject
    rpc_request.roles = roles
    rpc_request.role_mask = mask
    identity_source = 'mtls'
    _logger.debug('[RPC] Resolved MTLS roles for %s: %s (mask=%#018x)', mtls_subject, roles, mask)

  if domain == 'discord':
    discord_id = _get_discord_id_from_request(request)
    if not discord_id:
      raise HTTPException(status_code=401, detail='Discord identity assertion missing')
    guid, roles, mask = await auth.get_discord_user_security(discord_id)
    if not guid:
      raise HTTPException(status_code=403, detail='Forbidden')
    try:
      registered_mask = auth.require_role_mask('ROLE_REGISTERED')
    except KeyError as exc:
      message = 'Required role is undefined: ROLE_REGISTERED'
      _logger.error('[RPC] %s', message)
      raise HTTPException(status_code=500, detail=message) from exc
    if not (mask & registered_mask):
      raise HTTPException(status_code=403, detail='Forbidden')
    auth_ctx.user_guid = guid
    auth_ctx.roles = roles
    auth_ctx.role_mask = mask
    rpc_request.user_guid = guid
    rpc_request.roles = roles
    rpc_request.role_mask = mask
    identity_source = 'discord'
    _logger.debug('[RPC] Resolved Discord roles for %s: %s (mask=%#018x)', guid, roles, mask)
  elif domain not in ('public', 'auth') and not identity_source:
    raise HTTPException(status_code=401, detail='Missing or invalid authorization header')

  if identity_source:
    audit_payload = {
      'event': 'rpc.request.validated',
      'op': rpc_request.op,
      'domain': domain,
      'user_guid': auth_ctx.user_guid,
      'role_mask': auth_ctx.role_mask,
      'roles': auth_ctx.roles,
      'identity_source': identity_source,
    }
    if discord_id:
      audit_payload['discord_id'] = discord_id
    if token:
      audit_payload['token_present'] = True
    if mtls_subject:
      audit_payload['mtls_subject'] = mtls_subject
    _audit_logger.info('rpc.request.validated', extra=audit_payload)

  return auth_ctx


async def _process_rpcrequest(request: Request) -> tuple[RPCRequest, AuthContext]:
  body = await request.json()
  rpc_request = RPCRequest(**body)
  parts = rpc_request.op.split(':')
  auth_ctx = await _validate_rpc_identity(request, rpc_request, parts)
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
