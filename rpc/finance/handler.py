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
  subdomain = parts[0]

  requires_system_admin = False
  if subdomain == "staging_account_map":
    requires_system_admin = True
  elif subdomain == "staging" and len(parts) >= 3 and parts[1] == "promote" and parts[2] == "1":
    requires_system_admin = True

  role_name = "ROLE_SYSTEM_ADMIN" if requires_system_admin else "ROLE_FINANCE_ADMIN"
  required_mask = auth.roles.get(role_name, 0)
  if not await auth.user_has_role(auth_ctx.user_guid, required_mask):
    raise HTTPException(status_code=403, detail="Forbidden")

  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
  return await handler(parts[1:], request)
