"""Handlers for the Discord RPC namespace."""

from fastapi import HTTPException, Request

from rpc.dependencies import get_auth_service
from rpc.helpers import resolve_required_mask, unbox_request
from server.models import RPCResponse
from server.modules import AuthService

from . import FORBIDDEN_DETAILS, HANDLERS, REQUIRED_ROLES


async def handle_discord_request(parts: list[str], request: Request) -> RPCResponse:
  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthService = get_auth_service(request)
  role_name = REQUIRED_ROLES.get(subdomain)
  required_mask = resolve_required_mask(auth, role_name) if role_name else 0
  if not await auth.user_has_role(auth_ctx.user_guid, required_mask):
    detail = FORBIDDEN_DETAILS.get(subdomain, 'Forbidden')
    raise HTTPException(status_code=403, detail=detail)
  return await handler(parts[1:], request)

