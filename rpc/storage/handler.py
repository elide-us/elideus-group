"""Storage RPC namespace.

Provides storage operations requiring ROLE_STORAGE.
Auth and public domains are exempt from role checks.
"""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS

REQUIRED_ROLE_MASK = 0x0000000000000002  # ROLE_STORAGE


async def handle_storage_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth
  if not await auth.user_has_role(auth_ctx.user_guid, REQUIRED_ROLE_MASK):
    raise HTTPException(status_code=403, detail='Forbidden')

  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)

