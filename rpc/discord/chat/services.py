from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  DiscordChatSummarizeChannelRequest1,
  DiscordChatSummarizeChannelResponse1,
  DiscordChatUwuChatRequest1,
  DiscordChatUwuChatResponse1,
)


async def discord_chat_summarize_channel_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  req = DiscordChatSummarizeChannelRequest1(**(rpc_request.payload or {}))
  payload = DiscordChatSummarizeChannelResponse1(
    summary=f"Summary for {req.channel_id}"
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
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
