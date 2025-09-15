"""Handlers for the Discord RPC namespace."""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import FORBIDDEN_DETAILS, HANDLERS, REQUIRED_ROLES


async def handle_discord_request(parts: list[str], request: Request) -> RPCResponse:
  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth
  role_name = REQUIRED_ROLES.get(subdomain)
  required_mask = auth.roles.get(role_name, 0) if role_name else 0
  if not await auth.user_has_role(auth_ctx.user_guid, required_mask):
    detail = FORBIDDEN_DETAILS.get(subdomain, 'Forbidden')
    raise HTTPException(status_code=403, detail=detail)
  return await handler(parts[1:], request)

