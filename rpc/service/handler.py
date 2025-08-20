"""Service RPC namespace.

Handles service operations requiring ROLE_SERVICE_ADMIN.
"""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import DISPATCHERS

REQUIRED_ROLE_MASK = 0x4000000000000000  # ROLE_SERVICE_ADMIN


async def handle_service_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth
  if not await auth.user_has_role(auth_ctx.user_guid, REQUIRED_ROLE_MASK):
    raise HTTPException(status_code=403, detail="Forbidden")

  key = tuple(parts[:2])
  handler = DISPATCHERS.get(key)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC operation")
  return await handler(request)
