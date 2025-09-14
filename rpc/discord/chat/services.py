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
  await module.log_conversation(
    "summary",
    guild_id,
    channel_id,
    f"hours={hours}",
    payload["summary"] or "",
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload,
    version=rpc_request.version,
  )


async def discord_chat_uwu_chat_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  req = DiscordChatUwuChatRequest1(**payload_dict)
  module: DiscordChatModule = request.app.state.discord_chat
  await module.on_ready()
  conv_id = await module.log_conversation(
    "uwu",
    req.guild_id,
    req.channel_id,
    req.message,
    "",
  )
  result = await module.uwu_chat(req.guild_id, req.channel_id, req.user_id, req.message)
  if conv_id:
    await module.update_conversation_output(
      conv_id, result.get("uwu_response_text", "")
    )
  payload = DiscordChatUwuChatResponse1(**result)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
