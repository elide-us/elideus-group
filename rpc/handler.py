import logging
from types import SimpleNamespace

from fastapi import HTTPException, Request
from starlette.datastructures import Headers

from rpc import HANDLERS
from rpc.helpers import unbox_request
from server.models import AuthContext, RPCRequest, RPCResponse


async def handle_rpc_request(request: Request) -> RPCResponse:
  rpc_request, _, parts = await unbox_request(request)
  return await _dispatch_rpc_request(request, rpc_request, parts)


async def dispatch_rpc_op(
  app,
  op: str,
  payload: dict | None = None,
  *,
  discord_ctx=None,
  headers: dict | None = None,
) -> RPCResponse:
  rpc_request = RPCRequest(op=op, payload=payload)
  parts = rpc_request.op.split(':')
  if parts[:1] != ['urn']:
    raise HTTPException(status_code=400, detail='Invalid URN prefix')

  normalized_ctx = _normalize_discord_ctx(discord_ctx)
  auth_ctx = await _resolve_auth_context(app, rpc_request, normalized_ctx)

  state = SimpleNamespace(rpc_request=rpc_request, auth_ctx=auth_ctx)
  if normalized_ctx:
    setattr(state, 'discord_ctx', normalized_ctx)

  request = SimpleNamespace(
    app=app,
    state=state,
    headers=Headers(headers or {}),
  )

  return await _dispatch_rpc_request(request, rpc_request, parts)


async def _dispatch_rpc_request(request, rpc_request: RPCRequest, parts: list[str]) -> RPCResponse:
  if parts[:1] != ['urn']:
    raise HTTPException(status_code=400, detail='Invalid URN prefix')
  try:
    domain = parts[1]
    remainder = parts[2:]
    handler = HANDLERS.get(domain)
    if not handler:
      raise HTTPException(status_code=404, detail='Unknown RPC domain')
    response = await handler(remainder, request)
    logging.info(f"RPC completed: {rpc_request.op}")
    return response
  except Exception:
    logging.exception(f"RPC failed: {rpc_request.op}")
    raise


def _normalize_discord_ctx(discord_ctx):
  if not discord_ctx:
    return None
  if getattr(discord_ctx, 'author', None):
    return discord_ctx
  if isinstance(discord_ctx, dict):
    data = discord_ctx
  else:
    data = getattr(discord_ctx, '__dict__', {})
  author_id = data.get('user_id') or data.get('author_id')
  guild_id = data.get('guild_id')
  channel_id = data.get('channel_id')
  author = SimpleNamespace(id=author_id) if author_id is not None else None
  guild = SimpleNamespace(id=guild_id) if guild_id is not None else None
  channel = SimpleNamespace(id=channel_id) if channel_id is not None else None
  return SimpleNamespace(author=author, guild=guild, channel=channel)


async def _resolve_auth_context(app, rpc_request: RPCRequest, discord_ctx) -> AuthContext:
  auth_ctx = AuthContext()
  parts = rpc_request.op.split(':')
  domain = parts[1] if len(parts) > 1 else ''

  if domain == 'discord':
    auth = getattr(app.state, 'auth', None)
    if not auth:
      raise RuntimeError('Auth module is not configured on the application state')
    discord_id = None
    if discord_ctx and getattr(discord_ctx, 'author', None):
      discord_id = getattr(discord_ctx.author, 'id', None)
    if not discord_id and rpc_request.payload:
      discord_id = rpc_request.payload.get('discord_id') or rpc_request.payload.get('user_id')
    if not discord_id:
      raise HTTPException(status_code=401, detail='Missing or invalid authorization header')
    discord_id = str(discord_id)
    guid, roles, mask = await auth.get_discord_user_security(discord_id)
    if not guid:
      raise HTTPException(status_code=401, detail='Missing or invalid authorization header')
    auth_ctx.user_guid = guid
    auth_ctx.roles = roles
    auth_ctx.role_mask = mask
    rpc_request.user_guid = guid
    rpc_request.roles = roles
    rpc_request.role_mask = mask
    if not (mask & getattr(auth, 'role_registered', 0)):
      raise HTTPException(status_code=403, detail='Forbidden')
    logging.debug(
      "[RPC] Resolved roles for %s: %s (mask=%#018x)",
      guid,
      roles,
      mask,
    )
  elif domain not in ('public', 'auth'):
    raise HTTPException(status_code=401, detail='Missing or invalid authorization header')

  return auth_ctx

