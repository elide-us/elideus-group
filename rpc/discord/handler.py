"""Handlers for the Discord RPC namespace.

Requires ROLE_DISCORD_BOT.
"""

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from . import HANDLERS


async def handle_discord_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await unbox_request(request)
  auth: AuthModule = request.app.state.auth
  required_mask = auth.roles.get("ROLE_DISCORD_BOT", 0)
  if not await auth.user_has_role(auth_ctx.user_guid, required_mask):
    raise HTTPException(
      status_code=403,
      detail='You must have the Discord bot role assigned to use this bot.'
    )

  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)

