"""Handlers for the Discord RPC namespace."""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS


async def handle_discord_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  if not parts:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')

  auth: AuthModule = request.app.state.auth
  await auth.check_domain_access('discord', auth_ctx.user_guid)

  handler = HANDLERS.get(parts[0])
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)
