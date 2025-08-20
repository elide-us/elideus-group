"""Security RPC namespace.

Handles security operations requiring ROLE_SECURITY_ADMIN.
Auth and public domains are exempt from role checks.
"""

from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS

REQUIRED_ROLE_MASK = 0x1000000000000000  # ROLE_SECURITY_ADMIN
SYSTEM_ADMIN_MASK = 0x2000000000000000  # ROLE_SYSTEM_ADMIN


async def handle_security_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await get_rpcrequest_from_request(request)
  auth: AuthModule = request.app.state.auth

  subdomain = parts[0]
  action = parts[1] if len(parts) > 1 else ""
  required = REQUIRED_ROLE_MASK

  if subdomain == "roles" and action == "get_roles":
    if await auth.user_has_role(auth_ctx.user_guid, SYSTEM_ADMIN_MASK):
      required = 0

  if required and not await auth.user_has_role(auth_ctx.user_guid, required):
    raise HTTPException(status_code=403, detail='Forbidden')

  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)

