import logging
from typing import Any

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  DiscordChatPersonaRequest1,
  DiscordChatPersonaResponse1,
  DiscordChatSummarizeChannelRequest1,
  DiscordChatSummarizeChannelResponse1,
)

async def discord_chat_summarize_channel_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  input_payload = DiscordChatSummarizeChannelRequest1(**(rpc_request.payload or {}))
  module: Any = request.app.state.discord_chat
  await module.on_ready()
  result: DiscordChatSummarizeChannelResponse1 = await module.summarize_and_deliver(
    guild_id=input_payload.guild_id,
    channel_id=input_payload.channel_id,
    hours=input_payload.hours,
    user_id=input_payload.user_id,
  )
  response = DiscordChatSummarizeChannelResponse1(**result)
  return RPCResponse(
    op=rpc_request.op,
    payload=response.model_dump(),
    version=rpc_request.version,
  )


async def discord_chat_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  req = DiscordChatPersonaRequest1(**payload_dict)
  module: Any = request.app.state.openai
  await module.on_ready()
  try:
    result: DiscordChatPersonaResponse1 = await module.persona_response(
      req.persona,
      req.message,
      guild_id=req.guild_id,
      channel_id=req.channel_id,
      user_id=req.user_id,
    )
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = DiscordChatPersonaResponse1(
    persona=result.get("persona", ""),
    persona_response_text=result.get("response_text", ""),
    model=result.get("model"),
    role=result.get("role"),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
