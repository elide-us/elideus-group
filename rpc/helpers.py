from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException as FastAPIHTTPException
from fastapi import Request

from server.models import AuthContext
from server.models import RPCRequest
from server.errors import (
  RPCServiceError,
  bad_request,
  forbidden,
  internal_error,
  service_unavailable,
  unauthorized,
)
if TYPE_CHECKING:
  from server.modules import AuthService


def mask_to_bit(mask: int) -> int:
  if mask == 0:
    return 0
  return (mask.bit_length() - 1)

def bit_to_mask(bit: int) -> int:
  if bit < 0 or bit >= 63:
    raise bad_request('Invalid bit index', diagnostic=f'Bit index {bit} out of range')
  return 1 << bit

def _get_token_from_request(request: Request) -> str | None:
  header = request.headers.get('authorization')
  if not header or not header.lower().startswith('bearer '):
    logging.debug("No bearer token found in request headers")
    return None
  return header.split(' ', 1)[1].strip()

_logger = logging.getLogger(__name__)
_audit_logger = logging.getLogger('security.audit')

def _get_discord_metadata(request: Request) -> dict[str, str] | None:
  metadata = getattr(request.state, 'discord_metadata', None)
  if metadata:
    user_id = metadata.get('user_id') or metadata.get('id')
    if user_id:
      result: dict[str, str] = {'user_id': str(user_id)}
      guild_id = metadata.get('guild_id')
      channel_id = metadata.get('channel_id')
      if guild_id is not None:
        result['guild_id'] = str(guild_id)
      if channel_id is not None:
        result['channel_id'] = str(channel_id)
      return result
  ctx = getattr(request.state, 'discord_ctx', None)
  if ctx and getattr(ctx, 'author', None):
    author = ctx.author
    result = {'user_id': str(getattr(author, 'id', ''))}
    guild_id = getattr(ctx, 'guild_id', None)
    channel_id = getattr(ctx, 'channel_id', None)
    if guild_id is not None:
      result['guild_id'] = str(guild_id)
    if channel_id is not None:
      result['channel_id'] = str(channel_id)
    return result
  header_id = request.headers.get('x-discord-id') or request.headers.get('x-discord-user-id')
  if header_id:
    # Future webhook integrations may still rely on headers. Guard their usage so
    # internal callers must prefer structured metadata on request.state.
    result = {'user_id': str(header_id)}
    guild_id = request.headers.get('x-discord-guild-id')
    channel_id = request.headers.get('x-discord-channel-id')
    if guild_id is not None:
      result['guild_id'] = str(guild_id)
    if channel_id is not None:
      result['channel_id'] = str(channel_id)
    return result
  return None


def _get_mtls_subject(request: Request) -> str | None:
  subject = getattr(request.state, 'mtls_subject_guid', None)
  if subject:
    return str(subject)
  header_subject = request.headers.get('x-mtls-subject-guid')
  if header_subject:
    return str(header_subject)
  return None


def resolve_required_mask(auth: 'AuthService', role_name: str, *, context: str | None = None) -> int:
  if not role_name:
    raise internal_error('Role name must be provided', code='rpc.role.missing')
  try:
    return auth.require_role_mask(role_name)
  except KeyError as exc:
    message = f'Required role is undefined: {role_name}'
    _logger.error('[RPC] %s', message)
    audit_payload = {
      'event': 'rpc.role.undefined',
      'role': role_name,
      'context': context or 'rpc.resolve_required_mask',
    }
    _audit_logger.error('rpc.role.undefined', extra=audit_payload)
    raise forbidden('Forbidden', code='rpc.role.undefined', diagnostic=message) from exc


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
    raise service_unavailable(
      'Authentication module is unavailable',
      code='rpc.auth.unavailable',
      diagnostic='Authentication module is missing from app state',
    )

  identity_source = None
  discord_id: str | None = None
  discord_metadata = _get_discord_metadata(request)

  if domain == 'webhook' and not (token or mtls_subject):
    raise unauthorized(
      'Signed token or MTLS assertion required',
      code='rpc.auth.signature_required',
      diagnostic='Webhook request missing token or MTLS assertion',
    )

  if token:
    try:
      data: dict = await auth.decode_session_token(token)
    except RPCServiceError:
      raise
    except FastAPIHTTPException as exc:
      raise internal_error('Authentication failure', diagnostic=str(exc)) from exc
    except Exception as exc:
      _logger.exception('[RPC] Failed to decode session token')
      raise unauthorized('Invalid authorization token', diagnostic=str(exc)) from exc
    user_guid = data.get('sub')
    if not user_guid:
      raise unauthorized('Invalid authorization token payload', diagnostic='Missing sub claim')
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

  if domain == 'discord' and not identity_source:
    if not discord_metadata:
      raise unauthorized(
        'Discord identity assertion missing',
        diagnostic='Discord request missing metadata',
      )
    discord_id = discord_metadata.get('user_id')
    if not discord_id:
      raise unauthorized('Discord identity assertion missing', diagnostic='Discord metadata missing user id')
    guid, roles, mask = await auth.get_discord_user_security(discord_id)
    if not guid:
      raise forbidden('Forbidden', diagnostic=f'No Discord user for {discord_id}')
    registered_mask = resolve_required_mask(auth, 'ROLE_REGISTERED', context='discord.identity')
    if not (mask & registered_mask):
      raise forbidden('Forbidden', diagnostic=f'Discord user {guid} missing ROLE_REGISTERED')
    auth_ctx.user_guid = guid
    auth_ctx.roles = roles
    auth_ctx.role_mask = mask
    rpc_request.user_guid = guid
    rpc_request.roles = roles
    rpc_request.role_mask = mask
    identity_source = 'discord'
    _logger.debug('[RPC] Resolved Discord roles for %s: %s (mask=%#018x)', guid, roles, mask)
  elif domain not in ('public', 'auth') and not identity_source:
    raise unauthorized(
      'Missing or invalid authorization header',
      diagnostic='Protected domain without token or MTLS assertion',
    )

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
    if discord_metadata:
      guild_id = discord_metadata.get('guild_id')
      channel_id = discord_metadata.get('channel_id')
      if guild_id:
        audit_payload['discord_guild_id'] = guild_id
      if channel_id:
        audit_payload['discord_channel_id'] = channel_id
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
