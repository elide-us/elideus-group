"""Storage RPC namespace.

Provides storage operations requiring ROLE_STORAGE.
Auth and public domains are exempt from role checks.
"""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS


async def handle_storage_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  if not parts:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')

  auth: AuthModule = request.app.state.auth
  await auth.check_domain_access('storage', auth_ctx.user_guid)

  handler = HANDLERS.get(parts[0])
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)
