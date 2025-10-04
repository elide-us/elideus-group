"""Account RPC namespace.

Handles account operations requiring ROLE_ACCOUNT_ADMIN.
"""

from fastapi import HTTPException, Request

from rpc.dependencies import get_auth_service
from rpc.helpers import resolve_required_mask, unbox_request
from server.models import RPCResponse
from server.modules import AuthService
from . import HANDLERS


async def handle_account_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthService = get_auth_service(request)
  required_mask = resolve_required_mask(auth, "ROLE_ACCOUNT_ADMIN")
  if not await auth.user_has_role(auth_ctx.user_guid, required_mask):
    raise HTTPException(status_code=403, detail="Forbidden")

  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
  return await handler(parts[1:], request)
