from __future__ import annotations

import logging
import uuid
from typing import Any

from pydantic import BaseModel

from queryregistry.discord.channels import bump_activity_request
from queryregistry.discord.channels.models import BumpChannelActivityParams
from server.modules.async_task_handlers import PipelineHandler


class PersonaConversationPayload(BaseModel):
  persona_name: str
  message: str
  source_type: str = "discord"
  guild_id: str | None = None
  channel_id: str | None = None
  user_id: str | None = None


class PersonaConversationPipelineHandler(PipelineHandler):
  payload_model = PersonaConversationPayload

  steps = [
    ("parse_input", lambda app, payload, context: PersonaConversationPipelineHandler.parse_input(app, payload, context)),
    ("resolve_persona", lambda app, payload, context: PersonaConversationPipelineHandler.resolve_persona(app, payload, context)),
    ("gather_stored_context", lambda app, payload, context: PersonaConversationPipelineHandler.gather_stored_context(app, payload, context)),
    ("gather_channel_context", lambda app, payload, context: PersonaConversationPipelineHandler.gather_channel_context(app, payload, context)),
    ("assemble_prompt", lambda app, payload, context: PersonaConversationPipelineHandler.assemble_prompt(app, payload, context)),
    ("generate_response", lambda app, payload, context: PersonaConversationPipelineHandler.generate_response(app, payload, context)),
    ("log_and_deliver", lambda app, payload, context: PersonaConversationPipelineHandler.log_and_deliver(app, payload, context)),
  ]

  @staticmethod
  async def parse_input(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del app
    del context
    persona_name = str(payload.get("persona_name") or "").strip()
    message = str(payload.get("message") or "").strip()
    source_type = str(payload.get("source_type") or "discord").strip() or "discord"

    if not persona_name:
      raise ValueError("persona_name is required")
    if not message:
      raise ValueError("message is required")

    return {
      "persona_name": persona_name,
      "message": message,
      "source_type": source_type,
    }

  @staticmethod
  async def resolve_persona(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    openai = app.state.openai
    await openai.on_ready()

    persona_name = context["persona_name"]
    persona_details = await openai.get_persona_definition(persona_name)
    if not persona_details:
      raise ValueError(f"Persona '{persona_name}' not found")

    return {
      "persona_details": persona_details,
      "system_prompt": persona_details.get("prompt") or "",
      "model": persona_details.get("model"),
      "max_tokens": persona_details.get("tokens"),
      "personas_recid": persona_details.get("recid"),
      "models_recid": persona_details.get("models_recid"),
    }

  @staticmethod
  async def gather_stored_context(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    guild_id = payload.get("guild_id")
    channel_id = payload.get("channel_id")
    if not guild_id or not channel_id:
      return {"stored_context": []}

    openai = app.state.openai
    await openai.on_ready()

    try:
      stored_context = await openai.get_channel_context(str(guild_id), str(channel_id), limit=20)
      return {"stored_context": stored_context or []}
    except Exception:
      logging.exception(
        "[PersonaConversationPipelineHandler] gather_stored_context failed",
        extra={"guild_id": guild_id, "channel_id": channel_id},
      )
      return {"stored_context": []}

  @staticmethod
  async def gather_channel_context(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    source_type = str(payload.get("source_type") or "discord")
    guild_id = payload.get("guild_id")
    channel_id = payload.get("channel_id")

    if source_type != "discord" or not guild_id or not channel_id:
      return {"channel_history": []}

    discord_chat = getattr(app.state, "discord_chat", None)
    if discord_chat is None:
      return {"channel_history": []}

    await discord_chat.on_ready()

    try:
      history = await discord_chat.fetch_channel_history_backwards(
        int(guild_id),
        int(channel_id),
        hours=1,
        max_messages=200,
      )
      messages = history.get("messages") or []
      channel_history = [
        {
          "author": str(getattr(message, "author", "")),
          "content": str(getattr(message, "content", "") or ""),
        }
        for message in messages
        if str(getattr(message, "content", "") or "").strip()
      ]
      return {"channel_history": channel_history}
    except Exception:
      logging.exception(
        "[PersonaConversationPipelineHandler] gather_channel_context failed",
        extra={"guild_id": guild_id, "channel_id": channel_id},
      )
      return {"channel_history": []}

  @staticmethod
  async def assemble_prompt(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del app
    sections: list[str] = []

    stored_context = context.get("stored_context") or []
    if stored_context:
      stored_lines = [
        f"{str(item.get('role') or '')}: {str(item.get('content') or '')}"
        for item in stored_context[-15:]
        if str(item.get("content") or "").strip()
      ]
      if stored_lines:
        sections.append("Recent stored conversation context:\n" + "\n".join(stored_lines))

    channel_history = context.get("channel_history") or []
    if channel_history:
      channel_lines = [
        f"{str(item.get('author') or '')}: {str(item.get('content') or '')}"
        for item in channel_history[-20:]
        if str(item.get("content") or "").strip()
      ]
      if channel_lines:
        sections.append("Recent channel activity:\n" + "\n".join(channel_lines))

    prompt_context = "\n\n".join(sections)
    thread_id = f"discord:{payload.get('guild_id') or 0}:{payload.get('channel_id') or 0}:{uuid.uuid4().hex[:12]}"

    return {
      "prompt_context": prompt_context,
      "thread_id": thread_id,
    }

  @staticmethod
  async def generate_response(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    openai = app.state.openai
    await openai.on_ready()

    result = await openai.generate_chat(
      system_prompt=context["system_prompt"],
      user_prompt=payload["message"],
      model=context.get("model"),
      max_tokens=context.get("max_tokens"),
      prompt_context=context.get("prompt_context", ""),
    )

    return {
      "response_text": result["content"],
      "response_model": result.get("model", ""),
      "usage": result.get("usage"),
    }

  @staticmethod
  async def log_and_deliver(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    openai = app.state.openai
    await openai.on_ready()

    await openai.log_message(
      personas_recid=context["personas_recid"],
      models_recid=context["models_recid"],
      role="user",
      content=payload["message"],
      guild_id=payload.get("guild_id"),
      channel_id=payload.get("channel_id"),
      user_id=payload.get("user_id"),
      thread_id=context["thread_id"],
    )
    await openai.log_message(
      personas_recid=context["personas_recid"],
      models_recid=context["models_recid"],
      role="assistant",
      content=context["response_text"],
      guild_id=payload.get("guild_id"),
      channel_id=payload.get("channel_id"),
      user_id=payload.get("user_id"),
      thread_id=context["thread_id"],
    )

    delivered = False
    if str(payload.get("source_type") or "discord") == "discord" and payload.get("channel_id"):
      discord_output = getattr(app.state, "discord_output", None)
      if discord_output is not None:
        await discord_output.queue_channel_message(int(payload["channel_id"]), context["response_text"])
        delivered = True

      db = getattr(app.state, "db", None)
      if db is not None:
        await db.on_ready()
        await db.run(
          bump_activity_request(
            BumpChannelActivityParams(channel_id=str(payload["channel_id"]))
          )
        )

    return {
      "delivered": delivered,
      "delivery_target": "discord_channel" if delivered else "none",
    }
