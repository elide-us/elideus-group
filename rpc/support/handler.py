"""Support RPC namespace.

Handles support operations requiring ROLE_SUPPORT.
Auth and public domains are exempt from role checks.
"""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS

REQUIRED_ROLE_MASK = 0x0400000000000000  # ROLE_SUPPORT


async def handle_support_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth
  if not await auth.user_has_role(auth_ctx.user_guid, REQUIRED_ROLE_MASK):
    raise HTTPException(status_code=403, detail='Forbidden')

  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)
