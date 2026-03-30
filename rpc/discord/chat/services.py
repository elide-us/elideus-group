import logging

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.discord_chat_module import DiscordChatModule
from server.modules.openai_module import OpenaiModule
from server.modules.workflow_module import WorkflowModule

from .models import (
  DiscordChatPersonaRequest1,
  DiscordChatPersonaResponse1,
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
  module: OpenaiModule = request.app.state.openai
  await module.on_ready()
  try:
    result = await module.persona_response(
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
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "invalid_persona_usage",
        "ack_message": "Usage: !persona <persona> <message>",
      },
      version=rpc_request.version,
    )

  workflow: WorkflowModule = request.app.state.workflow
  await workflow.on_ready()

  # Fetch channel history from Discord before submitting the workflow.
  # This is transport-specific data that the generic pipeline steps don't fetch.
  channel_history = []
  discord_chat: DiscordChatModule | None = getattr(request.app.state, "discord_chat", None)
  if discord_chat:
    await discord_chat.on_ready()
    try:
      history_result = await discord_chat.get_channel_history(
        int(payload.get("guild_id") or 0),
        int(payload.get("channel_id") or 0),
      )
      channel_history = history_result.get("channel_history") or []
    except Exception:
      logging.exception("[discord_chat_persona_command_v1] failed to fetch channel history")

  workflow_payload = {
    "persona_name": persona,
    "user_message": message,
    "source": "discord",
    "guild_id": str(payload.get("guild_id") or ""),
    "channel_id": str(payload.get("channel_id") or ""),
    "user_id": str(payload.get("user_id") or ""),
    "channel_history": channel_history,
    "delivery_targets": ["discord_channel"],
  }

  try:
    run = await workflow.submit(
      "persona_conversation",
      workflow_payload,
      source_type="discord",
      source_id=str(payload.get("channel_id") or ""),
      timeout_seconds=120,
    )
    # Execute synchronously — the RPC caller waits for completion
    completed = await workflow.execute(run["guid"])
    context = completed.get("context") or {}

    success = completed.get("status") == 4  # STATUS_COMPLETED
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": success,
        "reason": "persona_response_delivered" if success else (completed.get("error") or "workflow_failed"),
        "ack_message": "Persona response delivered." if success else (completed.get("error") or "Persona chat is currently unavailable."),
        "response_text": context.get("response_text", ""),
        "model": context.get("model_used", ""),
        "thread_id": context.get("thread_id"),
      },
      version=rpc_request.version,
    )
  except Exception:
    logging.exception("[discord_chat_persona_command_v1] workflow execution failed")
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "workflow_execution_failed",
        "ack_message": "Persona chat is currently unavailable.",
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

  module: DiscordChatModule = request.app.state.discord_chat
  await module.on_ready()

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


async def discord_chat_deliver_persona_response_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  response = payload.get("response") or {}
  channel_id = payload.get("channel_id")
  user_id = payload.get("user_id")

  response_text = ""
  if isinstance(response, str):
    response_text = response
  elif isinstance(response, dict):
    response_text = response.get("text") or response.get("content") or ""

  discord_output = getattr(request.app.state, "discord_output", None)
  if not discord_output:
    return RPCResponse(
      op=rpc_request.op,
      payload={
        "success": False,
        "reason": "persona_delivery_failed",
        "ack_message": "Persona chat is currently unavailable.",
        "conversation_reference": payload.get("conversation_reference"),
      },
      version=rpc_request.version,
    )

  await discord_output.on_ready()
  success = False
  try:
    if channel_id is not None and response_text:
      await discord_output.queue_channel_message(int(channel_id), response_text)
      success = True
  except Exception:
    logging.exception("[discord_chat_deliver_persona_response_v1] failed to queue persona response")

  ack_message = "Persona response queued." if success else "Persona chat is currently unavailable."
  reason = "persona_response_queued" if success else "persona_delivery_failed"
  return RPCResponse(
    op=rpc_request.op,
    payload={
      "success": success,
      "reason": reason,
      "ack_message": ack_message,
      "conversation_reference": payload.get("conversation_reference"),
      "user_id": user_id,
    },
    version=rpc_request.version,
  )
