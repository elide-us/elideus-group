import logging

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.discord_chat_module import DiscordChatModule
from server.modules.openai_module import OpenaiModule

from .models import (
  DiscordChatPersonaRequest1,
  DiscordChatPersonaResponse1,
)


async def discord_chat_summarize_channel_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  p = rpc_request.payload or {}
  guild_id = p.get("guild_id")
  channel_id = p.get("channel_id")
  hours = int(p.get("hours", 1))
  user_id = p.get("user_id")
  if user_id is not None:
    user_id = int(user_id)
  if hours < 1 or hours > 336:
    raise ValueError("hours must be between 1 and 336")
  module: DiscordChatModule = request.app.state.discord_chat
  await module.on_ready()
  result = await module.summarize_chat(guild_id, channel_id, hours, user_id)
  payload = {
    "summary": result.get("summary_text"),
    "messages_collected": result.get("messages_collected"),
    "token_count_estimate": result.get("token_count_estimate"),
    "cap_hit": result.get("cap_hit"),
    "model": result.get("model"),
    "role": result.get("role"),
  }
  return RPCResponse(
    op=rpc_request.op,
    payload=payload,
    version=rpc_request.version,
  )


async def discord_chat_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  req = DiscordChatPersonaRequest1(**payload_dict)
  openai_module: OpenaiModule | None = getattr(request.app.state, "openai", None)
  if not openai_module:
    logging.warning("[discord_chat_persona_response_v1] OpenAI module not configured")
    raise HTTPException(status_code=503, detail="persona support unavailable")

  await openai_module.on_ready()
  try:
    result = await openai_module.persona_response(
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
