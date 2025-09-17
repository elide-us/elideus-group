from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import DiscordCommandGetRolesResponse1


async def discord_command_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = DiscordCommandGetRolesResponse1(roles=auth_ctx.roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

