"""Service RPC namespace.

Handles service operations requiring ROLE_SERVICE_ADMIN.
Role management subdomain operations require ROLE_ACCOUNT_ADMIN,
with ROLE_SYSTEM_ADMIN permitted to fetch role definitions.
"""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import DISPATCHERS, HANDLERS

REQUIRED_ROLE_MASK = 0x4000000000000000  # ROLE_SERVICE_ADMIN
ACCOUNT_ADMIN_MASK = 0x1000000000000000  # ROLE_ACCOUNT_ADMIN
SYSTEM_ADMIN_MASK = 0x2000000000000000  # ROLE_SYSTEM_ADMIN


async def handle_service_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth

  subdomain = parts[0]
  action = parts[1] if len(parts) > 1 else ""
  required = REQUIRED_ROLE_MASK

  if subdomain == "roles":
    required = ACCOUNT_ADMIN_MASK
    if action == "get_roles" and await auth.user_has_role(auth_ctx.user_guid, SYSTEM_ADMIN_MASK):
      required = 0

  if required and not await auth.user_has_role(auth_ctx.user_guid, required):
    raise HTTPException(status_code=403, detail="Forbidden")

  handler = HANDLERS.get(subdomain)
  if handler:
    return await handler(parts[1:], request)

  key = tuple(parts[:2])
  handler = DISPATCHERS.get(key)
  if handler:
    return await handler(request)

  raise HTTPException(status_code=404, detail="Unknown RPC operation")
