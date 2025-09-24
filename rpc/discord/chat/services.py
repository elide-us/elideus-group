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


def _persona_stub_response(rpc_request, detail: str) -> RPCResponse:
  logging.info("[discord_chat_persona_stub] %s", detail)
  payload = {
    "success": False,
    "reason": "not_implemented",
    "detail": detail,
    "ack_message": "Persona chat is currently unavailable.",
  }
  return RPCResponse(
    op=rpc_request.op,
    payload=payload,
    version=rpc_request.version,
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
  messages_collected = int(result.get("messages_collected") or 0)
  token_count_estimate = int(result.get("token_count_estimate") or 0)
  cap_hit = bool(result.get("cap_hit"))
  summary_text = result.get("summary_text") or ""
  reason = None
  success = True
  if messages_collected <= 0:
    success = False
    reason = "no_messages"
    ack_message = "No messages found in the specified time range"
  elif cap_hit:
    success = False
    reason = "cap_hit"
    ack_message = "Channel too active to summarize; message cap hit"
  elif not summary_text.strip():
    success = False
    reason = "empty_summary"
    ack_message = "Failed to generate summary. Please try again later."
  else:
    if user_id:
      ack_message = f"Summary queued for delivery to <@{user_id}>."
    else:
      ack_message = "Summary queued for delivery."
  try:
    ack = await module.deliver_summary(
      guild_id=guild_id,
      channel_id=channel_id,
      user_id=user_id,
      summary_text=summary_text if success else None,
      ack_message=ack_message,
      success=success,
      reason=reason,
      messages_collected=messages_collected,
      token_count_estimate=token_count_estimate,
      cap_hit=cap_hit,
    )
  except Exception:
    logging.exception(
      "[discord_chat_summarize_channel_v1] deliver_summary failed",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
      },
    )
    ack = {
      "success": False,
      "queue_id": None,
      "summary_success": False,
      "dm_enqueued": False,
      "channel_ack_enqueued": False,
      "reason": "delivery_failed",
      "ack_message": ack_message,
      "messages_collected": messages_collected,
      "token_count_estimate": token_count_estimate,
      "cap_hit": cap_hit,
    }
  payload = {
    "success": bool(ack.get("success")),
    "queue_id": ack.get("queue_id"),
    "messages_collected": messages_collected,
    "token_count_estimate": token_count_estimate,
    "cap_hit": cap_hit,
    "dm_enqueued": bool(ack.get("dm_enqueued")),
    "channel_ack_enqueued": bool(ack.get("channel_ack_enqueued")),
    "reason": ack.get("reason"),
    "ack_message": ack.get("ack_message"),
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


async def discord_chat_persona_command_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  return _persona_stub_response(
    rpc_request,
    "Persona command dispatch requires server module implementation.",
  )


async def discord_chat_get_persona_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  return _persona_stub_response(
    rpc_request,
    "Persona lookup via OpenAI module is not yet wired.",
  )


async def discord_chat_get_conversation_history_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  return _persona_stub_response(
    rpc_request,
    "Conversation history fetch from assistant_conversation is pending.",
  )


async def discord_chat_get_channel_history_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  return _persona_stub_response(
    rpc_request,
    "Channel history capture for persona workflow is not implemented.",
  )


async def discord_chat_insert_conversation_input_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  return _persona_stub_response(
    rpc_request,
    "Conversation input insertion requires server module support.",
  )


async def discord_chat_generate_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  return _persona_stub_response(
    rpc_request,
    "Persona response generation is pending OpenAI integration.",
  )


async def discord_chat_deliver_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  return _persona_stub_response(
    rpc_request,
    "Persona response delivery via Discord output module is not available yet.",
  )
