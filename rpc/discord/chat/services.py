from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.discord_chat_module import DiscordChatModule

from .models import (
  DiscordChatUwuChatRequest1,
  DiscordChatUwuChatResponse1,
)


async def discord_chat_summarize_channel_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  p = rpc_request.payload or {}
  guild_id = p.get("guild_id")
  channel_id = p.get("channel_id")
  hours = int(p.get("hours", 1))
  if hours < 1 or hours > 336:
    raise ValueError("hours must be between 1 and 336")
  module: DiscordChatModule = request.app.state.discord_chat
  await module.on_ready()
  summary = await module.summarize_channel(guild_id, channel_id, hours)
  payload = {
    "summary": summary.get("raw_text_blob"),
    "messages_collected": summary.get("messages_collected"),
    "token_count_estimate": summary.get("token_count_estimate"),
    "cap_hit": summary.get("cap_hit"),
  }
  return RPCResponse(
    op=rpc_request.op,
    payload=payload,
    version=rpc_request.version,
  )


async def discord_chat_uwu_chat_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  req = DiscordChatUwuChatRequest1(**(rpc_request.payload or {}))
  payload = DiscordChatUwuChatResponse1(message=f"uwu {req.message}")
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
