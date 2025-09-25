import logging
from datetime import datetime, timedelta, timezone
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
  if not persona:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "missing_persona",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  openai_module: OpenaiModule | None = getattr(request.app.state, "openai", None)
  if not openai_module:
    logging.warning("[discord_chat_get_persona_v1] OpenAI module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  await openai_module.on_ready()
  try:
    persona_details = await openai_module.get_persona_definition(persona)
  except Exception:
    logging.exception("[discord_chat_get_persona_v1] failed to load persona", extra={"persona": persona})
    persona_details = None

  if not persona_details:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_not_found",
        "ack_message": f"Persona '{persona}' was not found.",
      },
      version=rpc_request.version,
    )

  model = persona_details.get("model")
  tokens = persona_details.get("tokens")
  if isinstance(tokens, str):
    try:
      tokens = int(tokens)
    except ValueError:
      tokens = None

  payload_out: Dict[str, Any] = {
    "success": True,
    "persona_details": persona_details,
    "model": model,
  }
  if tokens is not None:
    payload_out["max_tokens"] = tokens

  return RPCResponse(
    op=rpc_request.op,
    payload=payload_out,
    version=rpc_request.version,
  )


async def discord_chat_get_conversation_history_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  persona = (payload.get("persona") or "").strip()
  if not persona:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "missing_persona",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  db_module = getattr(request.app.state, "db", None)
  openai_module: OpenaiModule | None = getattr(request.app.state, "openai", None)
  if not db_module or not openai_module:
    logging.warning(
      "[discord_chat_get_conversation_history_v1] required modules unavailable",
      extra={"has_db": bool(db_module), "has_openai": bool(openai_module)},
    )
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  await db_module.on_ready()
  await openai_module.on_ready()

  persona_details = await openai_module.get_persona_definition(persona)
  personas_recid = persona_details.get("recid") if persona_details else None
  if personas_recid is None:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_not_found",
        "ack_message": f"Persona '{persona}' was not found.",
      },
      version=rpc_request.version,
    )

  now = datetime.now(timezone.utc)
  start = now - timedelta(days=30)
  try:
    history_res = await db_module.run(
      "db:assistant:conversations:list_by_time:1",
      {
        "personas_recid": personas_recid,
        "start": start.isoformat(),
        "end": now.isoformat(),
      },
    )
  except Exception:
    logging.exception("[discord_chat_get_conversation_history_v1] db query failed")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "conversation_history_unavailable",
        "ack_message": "Failed to load previous persona conversation.",
      },
      version=rpc_request.version,
    )

  rows = list(history_res.rows or [])

  def _parse_timestamp(value: Any) -> datetime:
    if not value:
      return datetime.min.replace(tzinfo=timezone.utc)
    if isinstance(value, datetime):
      return value.astimezone(timezone.utc)
    if isinstance(value, str):
      candidate = value.replace("Z", "+00:00")
      try:
        return datetime.fromisoformat(candidate)
      except ValueError:
        pass
    return datetime.min.replace(tzinfo=timezone.utc)

  rows.sort(key=lambda row: _parse_timestamp(row.get("element_created_on")))
  recent_rows = rows[-5:]
  conversation_history: List[Dict[str, str]] = []
  for row in recent_rows:
    user_input = (row.get("element_input") or "").strip()
    if user_input:
      conversation_history.append({"role": "user", "content": user_input})
    assistant_output = (row.get("element_output") or "").strip()
    if assistant_output:
      conversation_history.append({"role": "assistant", "content": assistant_output})

  return RPCResponse(
    op=rpc_request.op,
    payload={
      "success": True,
      "conversation_history": conversation_history,
      "personas_recid": personas_recid,
      "models_recid": persona_details.get("models_recid") if persona_details else None,
    },
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

  await module.on_ready()
  try:
    history = await module.fetch_channel_history_backwards(
      guild_id_int,
      channel_id_int,
      hours=1,
      max_messages=200,
    )
  except Exception:
    logging.exception(
      "[discord_chat_get_channel_history_v1] failed to fetch channel history",
      extra={"guild_id": guild_id_int, "channel_id": channel_id_int},
    )
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "channel_history_unavailable",
        "ack_message": "Failed to fetch messages. Please try again later.",
      },
      version=rpc_request.version,
    )

  messages = history.get("messages") or []
  channel_history: List[Dict[str, Any]] = []
  for msg in messages:
    content = getattr(msg, "content", None)
    if not content:
      continue
    author = getattr(msg, "author", None)
    author_name = None
    if author is not None:
      author_name = getattr(author, "display_name", None) or getattr(author, "name", None) or getattr(author, "id", None)
    channel_history.append(
      {
        "author": str(author_name) if author_name is not None else "unknown",
        "content": str(content),
        "created_at": getattr(msg, "created_at", None),
      }
    )

  return RPCResponse(
    op=rpc_request.op,
    payload={"success": True, "channel_history": channel_history},
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

  db_module = getattr(request.app.state, "db", None)
  openai_module: OpenaiModule | None = getattr(request.app.state, "openai", None)
  if not db_module or not openai_module:
    logging.warning(
      "[discord_chat_insert_conversation_input_v1] required modules unavailable",
      extra={"has_db": bool(db_module), "has_openai": bool(openai_module)},
    )
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  await db_module.on_ready()
  await openai_module.on_ready()

  persona_details = payload.get("persona_details") or await openai_module.get_persona_definition(persona)
  if not persona_details:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_not_found",
        "ack_message": f"Persona '{persona}' was not found.",
      },
      version=rpc_request.version,
    )

  personas_recid = persona_details.get("recid")
  models_recid = persona_details.get("models_recid")
  if personas_recid is None or models_recid is None:
    logging.warning(
      "[discord_chat_insert_conversation_input_v1] persona missing identifiers",
      extra={"persona": persona},
    )
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_not_configured",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  guild_id = payload.get("guild_id")
  channel_id = payload.get("channel_id")
  user_id = payload.get("user_id")

  args = {
    "personas_recid": personas_recid,
    "models_recid": models_recid,
    "guild_id": str(guild_id) if guild_id is not None else None,
    "channel_id": str(channel_id) if channel_id is not None else None,
    "user_id": str(user_id) if user_id is not None else None,
    "input_data": message,
    "output_data": "",
    "tokens": None,
  }

  try:
    insert_res = await db_module.run("db:assistant:conversations:insert:1", args)
  except Exception:
    logging.exception("[discord_chat_insert_conversation_input_v1] insert failed", extra={"persona": persona})
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "conversation_log_failed",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  recid = None
  if insert_res.rows:
    recid = insert_res.rows[0].get("recid")

  return RPCResponse(
    op=rpc_request.op,
    payload={
      "success": True,
      "conversation_reference": recid,
      "personas_recid": personas_recid,
      "models_recid": models_recid,
    },
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

  openai_module: OpenaiModule | None = getattr(request.app.state, "openai", None)
  db_module = getattr(request.app.state, "db", None)
  if not openai_module:
    logging.warning("[discord_chat_generate_persona_response_v1] OpenAI module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  await openai_module.on_ready()
  persona_details = payload.get("persona_details") or await openai_module.get_persona_definition(persona)
  if not persona_details:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_not_found",
        "ack_message": f"Persona '{persona}' was not found.",
      },
      version=rpc_request.version,
    )

  model_hint = payload.get("model") or persona_details.get("model")
  max_tokens = payload.get("max_tokens") or persona_details.get("tokens")
  try:
    max_tokens = int(max_tokens) if max_tokens is not None else None
  except (TypeError, ValueError):
    max_tokens = None

  conversation_history = payload.get("conversation_history") or []
  channel_history = payload.get("channel_history") or []

  def _format_conversation(items: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for item in items[-10:]:
      role = item.get("role") or "user"
      content = item.get("content") or ""
      if not content:
        continue
      parts.append(f"{role}: {content}")
    return "\n".join(parts)

  def _format_channel(items: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for item in items[-20:]:
      author = item.get("author") or "unknown"
      content = item.get("content") or ""
      if not content:
        continue
      parts.append(f"{author}: {content}")
    return "\n".join(parts)

  context_sections: List[str] = []
  convo_text = _format_conversation(conversation_history)
  if convo_text:
    context_sections.append("Recent persona conversation:\n" + convo_text)
  channel_text = _format_channel(channel_history)
  if channel_text:
    context_sections.append("Recent channel activity:\n" + channel_text)
  prompt_context = "\n\n".join(context_sections)

  system_prompt = persona_details.get("prompt") or ""

  try:
    response = await openai_module.generate_chat(
      system_prompt=system_prompt,
      user_prompt=message,
      model=model_hint,
      max_tokens=max_tokens,
      prompt_context=prompt_context,
      persona=None,
      persona_details=None,
      guild_id=payload.get("guild_id"),
      channel_id=payload.get("channel_id"),
      user_id=payload.get("user_id"),
      input_log=message,
      token_count=None,
    )
  except Exception:
    logging.exception("[discord_chat_generate_persona_response_v1] OpenAI request failed", extra={"persona": persona})
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_generation_failed",
        "ack_message": "Failed to generate a persona response. Please try again later.",
      },
      version=rpc_request.version,
    )

  content = (response or {}).get("content") if isinstance(response, dict) else getattr(response, "content", "")
  model_used = (response or {}).get("model") if isinstance(response, dict) else getattr(response, "model", model_hint)
  usage = (response or {}).get("usage") if isinstance(response, dict) else getattr(response, "usage", None)

  total_tokens = None
  if isinstance(usage, dict):
    total_tokens = usage.get("total_tokens")

  conversation_reference = payload.get("conversation_reference")
  if db_module and conversation_reference is not None:
    await db_module.on_ready()
    try:
      await db_module.run(
        "db:assistant:conversations:update_output:1",
        {
          "recid": conversation_reference,
          "output_data": content or "",
          "tokens": total_tokens,
        },
      )
    except Exception:
      logging.exception(
        "[discord_chat_generate_persona_response_v1] failed to update conversation output",
        extra={"conversation_reference": conversation_reference},
      )

  return RPCResponse(
    op=rpc_request.op,
    payload={
      "success": True,
      "response": {"text": content or "", "model": model_used},
      "model": model_used,
      "usage": usage,
      "conversation_reference": conversation_reference,
    },
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

  output_module = getattr(request.app.state, "discord_output", None)
  if not output_module:
    logging.warning("[discord_chat_deliver_persona_response_v1] discord output module unavailable")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      },
      version=rpc_request.version,
    )

  await output_module.on_ready()
  success = False
  try:
    if channel_id is not None and response_text:
      await output_module.queue_channel_message(int(channel_id), response_text)
      success = True
  except Exception:
    logging.exception(
      "[discord_chat_deliver_persona_response_v1] failed to queue channel message",
      extra={"channel_id": channel_id},
    )
    success = False

  if success and user_id is not None:
    ack_message = f"Persona response queued for <@{user_id}>."
  elif success:
    ack_message = "Persona response queued."
  else:
    ack_message = "Persona chat is currently unavailable."

  reason = "persona_response_queued" if success else "persona_delivery_failed"

  return RPCResponse(
    op=rpc_request.op,
    payload={
      "success": success,
      "reason": reason,
      "ack_message": ack_message,
      "conversation_reference": payload.get("conversation_reference"),
    },
    version=rpc_request.version,
  )
