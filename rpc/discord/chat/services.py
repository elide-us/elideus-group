from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.discord_chat_module import DiscordChatModule
from server.modules.discord_personas_module import DiscordPersonasModule
from server.modules.personas_module import PersonasModule

from .models import (
  DiscordChatPersonaRequest1,
  DiscordChatPersonaResponse1,
  DiscordChatUwuChatRequest1,
  DiscordChatUwuChatResponse1,
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


async def discord_chat_uwu_chat_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  req = DiscordChatUwuChatRequest1(**payload_dict)
  module: DiscordChatModule = request.app.state.discord_chat
  await module.on_ready()
  result = await module.uwu_chat(req.guild_id, req.channel_id, req.user_id, req.message)
  payload = DiscordChatUwuChatResponse1(**result)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def discord_chat_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  req = DiscordChatPersonaRequest1(**payload_dict)
  persona_module: PersonasModule = request.app.state.personas
  await persona_module.on_ready()

  persona_name = (req.persona or "").strip()
  persona_prompt = None
  persona_model = None
  persona_registry: DiscordPersonasModule | None = getattr(request.app.state, "discord_personas", None)
  if persona_registry:
    await persona_registry.on_ready()
    try:
      personas = await persona_registry.list_personas()
    except Exception:
      personas = []
    normalized_name = persona_name.casefold()
    for persona_row in personas:
      candidate = (persona_row.get("name") or "").strip()
      if not candidate:
        continue
      if candidate.casefold() == normalized_name:
        persona_name = candidate
        persona_prompt = persona_row.get("prompt")
        persona_model = persona_row.get("model")
        break
  try:
    result = await persona_module.persona_response(
      persona_name,
      req.message,
      guild_id=req.guild_id,
      channel_id=req.channel_id,
      user_id=req.user_id,
    )
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = DiscordChatPersonaResponse1(
    persona=result.get("persona") or persona_name,
    persona_response_text=result.get("response_text", ""),
    model=result.get("model") or persona_model,
    role=result.get("role") or persona_prompt,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
