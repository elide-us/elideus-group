import logging
from typing import Any, Dict, List

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
  payload = rpc_request.payload or {}
  module: DiscordChatModule = request.app.state.discord_chat
  await module.on_ready()
  result = await module.summarize_and_deliver(
    guild_id=payload.get("guild_id"),
    channel_id=payload.get("channel_id"),
    hours=int(payload.get("hours", 1)),
    user_id=int(payload["user_id"]) if payload.get("user_id") is not None else None,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=result,
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
  payload = rpc_request.payload or {}
  persona = (payload.get("persona") or "").strip()
  message = (payload.get("message") or "").strip()
  if not persona or not message:
    logging.warning(
      "[discord_chat_persona_command_v1] invalid usage",
      extra={"persona": persona, "has_message": bool(message)},
    )
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "invalid_persona_usage",
        "ack_message": "Usage: !persona <persona> <message>",
      },
      version=rpc_request.version,
    )

  logging.info(
    "[discord_chat_persona_command_v1] received persona command",
    extra={
      "persona": persona,
      "guild_id": payload.get("guild_id"),
      "channel_id": payload.get("channel_id"),
      "user_id": payload.get("user_id"),
    },
  )

  return RPCResponse(
    op=rpc_request.op,
    payload={
      "success": True,
      "persona": persona,
      "message": message,
    },
    version=rpc_request.version,
  )


async def discord_chat_get_persona_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  persona = (payload.get("persona") or "").strip()
  module: DiscordChatModule | None = getattr(request.app.state, "discord_chat", None)
  if not module:
    logging.warning("[discord_chat_get_persona_v1] discord chat module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  result = await module.get_persona(
    persona,
    guild_id=payload.get("guild_id"),
    channel_id=payload.get("channel_id"),
    user_id=payload.get("user_id"),
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def discord_chat_get_conversation_history_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  persona = (payload.get("persona") or "").strip()
  module: DiscordChatModule | None = getattr(request.app.state, "discord_chat", None)
  if not module:
    logging.warning("[discord_chat_get_conversation_history_v1] discord chat module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  result = await module.get_conversation_history(
    persona,
    guild_id=payload.get("guild_id"),
    channel_id=payload.get("channel_id"),
    user_id=payload.get("user_id"),
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def discord_chat_get_channel_history_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  channel_id = payload.get("channel_id")
  guild_id = payload.get("guild_id")
  if channel_id is None or guild_id is None:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "missing_channel",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  try:
    channel_id_int = int(channel_id)
    guild_id_int = int(guild_id)
  except (TypeError, ValueError):
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "invalid_channel",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  module: DiscordChatModule | None = getattr(request.app.state, "discord_chat", None)
  if not module:
    logging.warning("[discord_chat_get_channel_history_v1] discord chat module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  result = await module.get_channel_history(
    guild_id_int,
    channel_id_int,
    persona=payload.get("persona"),
    user_id=payload.get("user_id"),
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def discord_chat_insert_conversation_input_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  persona = (payload.get("persona") or "").strip()
  message = (payload.get("message") or "").strip()
  if not persona or not message:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "invalid_persona_usage",
        "ack_message": "Usage: !persona <persona> <message>",
      },
      version=rpc_request.version,
    )

  module: DiscordChatModule | None = getattr(request.app.state, "discord_chat", None)
  if not module:
    logging.warning("[discord_chat_insert_conversation_input_v1] discord chat module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  result = await module.insert_conversation_input(
    persona,
    message,
    persona_details=payload.get("persona_details"),
    conversation_history=payload.get("conversation_history"),
    guild_id=payload.get("guild_id"),
    channel_id=payload.get("channel_id"),
    user_id=payload.get("user_id"),
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def discord_chat_generate_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  persona = (payload.get("persona") or "").strip()
  message = (payload.get("message") or "").strip()
  if not persona or not message:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "invalid_persona_usage",
        "ack_message": "Usage: !persona <persona> <message>",
      },
      version=rpc_request.version,
    )

  module: DiscordChatModule | None = getattr(request.app.state, "discord_chat", None)
  if not module:
    logging.warning("[discord_chat_generate_persona_response_v1] discord chat module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  result = await module.generate_persona_response(
    persona,
    message,
    persona_details=payload.get("persona_details"),
    conversation_history=payload.get("conversation_history"),
    channel_history=payload.get("channel_history"),
    model=payload.get("model"),
    max_tokens=payload.get("max_tokens"),
    conversation_reference=payload.get("conversation_reference"),
    personas_recid=payload.get("personas_recid"),
    models_recid=payload.get("models_recid"),
    guild_id=payload.get("guild_id"),
    channel_id=payload.get("channel_id"),
    user_id=payload.get("user_id"),
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def discord_chat_deliver_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  response = payload.get("response") or {}
  if isinstance(response, str):
    response_text = response
  else:
    response_text = response.get("text") or response.get("content") or ""
  channel_id = payload.get("channel_id")
  user_id = payload.get("user_id")

  module: DiscordChatModule | None = getattr(request.app.state, "discord_chat", None)
  if not module:
    logging.warning("[discord_chat_deliver_persona_response_v1] discord chat module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  result = await module.deliver_persona_response(
    persona=payload.get("persona", ""),
    response=response,
    conversation_reference=payload.get("conversation_reference"),
    guild_id=payload.get("guild_id"),
    channel_id=channel_id,
    user_id=user_id,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )
