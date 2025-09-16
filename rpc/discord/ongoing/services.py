from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.discord_ongoing_chat_module import DiscordOngoingChatModule

from .models import (
  DiscordOngoingCountdownResponse1,
  DiscordOngoingToggleActiveResponse1,
)


async def discord_ongoing_toggle_active_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module: DiscordOngoingChatModule = request.app.state.discord_ongoing_chat
  await module.on_ready()
  active = await module.toggle_active()
  payload = DiscordOngoingToggleActiveResponse1(active=active)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def discord_ongoing_countdown_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module: DiscordOngoingChatModule = request.app.state.discord_ongoing_chat
  await module.on_ready()
  seconds_remaining = await module.countdown_seconds()
  active = await module.is_active()
  payload = DiscordOngoingCountdownResponse1(
    active=active,
    seconds_remaining=seconds_remaining,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
