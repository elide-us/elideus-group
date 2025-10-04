"""Storage RPC namespace.

Provides storage operations requiring ROLE_STORAGE.
Auth and public domains are exempt from role checks.
"""

from fastapi import HTTPException, Request

from rpc.helpers import resolve_required_mask, unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS


async def handle_storage_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth
  required_mask = resolve_required_mask(auth, "ROLE_STORAGE")
  if not await auth.user_has_role(auth_ctx.user_guid, required_mask):
    raise HTTPException(status_code=403, detail='Forbidden')

  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)

