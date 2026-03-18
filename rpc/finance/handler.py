from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS


async def handle_finance_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  if not parts:
    raise HTTPException(status_code=404, detail="Unknown RPC subdomain")

  auth: AuthModule = request.app.state.auth
  required_mask = auth.roles.get("ROLE_FINANCE_ADMIN", 0)
  if not await auth.user_has_role(auth_ctx.user_guid, required_mask):
    raise HTTPException(status_code=403, detail="Forbidden")

  handler = HANDLERS.get(parts[0])
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
  return await handler(parts[1:], request)
