"""Discord chat utilities module."""

import logging, time, discord, uuid
from queryregistry.discord.channels import bump_activity_request
from queryregistry.discord.channels.models import BumpChannelActivityParams
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from typing import Any, Dict, List

from . import BaseModule
from .discord_bot_module import DiscordBotModule
from .db_module import DbModule


class DiscordChatModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordBotModule | None = None

  async def startup(self):
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    self.app.state.discord_chat = self
    logging.debug("[DiscordChatModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    logging.info("[DiscordChatModule] shutdown")

  def _generate_thread_id(self, guild_id: int | None, channel_id: int | None) -> str:
    """Generate a thread ID for a persona conversation session.

    Format: discord:{guild_id}:{channel_id}:{session_uuid}
    Each command invocation starts a new thread to group the
    user message and assistant response together.
    """
    g = str(guild_id) if guild_id is not None else "0"
    c = str(channel_id) if channel_id is not None else "0"
    return f"discord:{g}:{c}:{uuid.uuid4().hex[:12]}"

  async def _bump_channel_activity(self, metadata: dict) -> None:
    if not metadata.get("channel_id"):
      return
    try:
      db: DbModule = getattr(self.app.state, "db", None)
      if db:
        await db.run(
          bump_activity_request(BumpChannelActivityParams(
            channel_id=str(metadata["channel_id"]),
          ))
        )
    except Exception:
      logging.debug(
        "[DiscordChatModule] channel activity bump failed (channel may not be registered)",
        extra={"channel_id": metadata.get("channel_id")},
      )

  async def fetch_channel_history_backwards(self, guild_id: int, channel_id: int, hours: int, max_messages: int = 5000) -> dict:
    assert self.discord and self.discord.bot
    start = time.perf_counter()
    guild = self.discord.bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if not channel:
      return {"messages": [], "cap_hit": False}
    after = datetime.now(timezone.utc) - timedelta(hours=hours)
    messages: List[discord.Message] = []
    try:
      async for msg in channel.history(limit=max_messages, after=after, oldest_first=False):
        messages.append(msg)
    except Exception:
      logging.exception("[DiscordChatModule] fetch_channel_history_backwards failed")
      raise
    messages.reverse()
    cap_hit = len(messages) >= max_messages
    elapsed = time.perf_counter() - start
    logging.info(
      "[DiscordChatModule] fetch_channel_history_backwards",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "hours": hours,
        "messages_collected": len(messages),
        "cap_hit": cap_hit,
        "elapsed": elapsed,
      },
    )
    return {"messages": messages, "cap_hit": cap_hit}

  def estimate_tokens(self, text: str) -> int:
    try:
      import tiktoken
      enc = tiktoken.get_encoding("cl100k_base")
      return len(enc.encode(text))
    except Exception:
      return len(text.split())

  async def summarize_channel(self, guild_id: int, channel_id: int, hours: int, max_messages: int = 5000) -> dict:
    start = time.perf_counter()
    history = await self.fetch_channel_history_backwards(guild_id, channel_id, hours, max_messages)
    messages = history["messages"]
    lines = [f"{m.author.name}: {m.content}" for m in messages if getattr(m, "content", None)]
    raw_text_blob = "\n".join(lines)
    tokens = self.estimate_tokens(raw_text_blob)
    elapsed = time.perf_counter() - start
    logging.info(
      "[DiscordChatModule] summarize_channel",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "hours": hours,
        "messages_collected": len(messages),
        "token_count_estimate": tokens,
        "cap_hit": history["cap_hit"],
        "elapsed": elapsed,
      },
    )
    return {
      "messages_collected": len(messages),
      "token_count_estimate": tokens,
      "raw_text_blob": raw_text_blob,
      "cap_hit": history["cap_hit"],
    }

  async def summarize_chat(
    self,
    guild_id: int,
    channel_id: int,
    hours: int,
    user_id: int | None = None,
    max_messages: int = 5000,
  ) -> dict:
    hours = max(hours, 1)
    start = time.perf_counter()
    summary = await self.summarize_channel(guild_id, channel_id, hours, max_messages)
    openai = getattr(self.app.state, "openai", None)
    summary_text = ""
    model = ""
    role = ""
    persona_name = "summarize"
    if openai:
      await openai.on_ready()
      persona_details = None
      try:
        persona_details = await openai.get_persona_definition(persona_name)
      except Exception:
        logging.exception(
          "[DiscordChatModule] failed to load summarize persona",
          extra={"persona": persona_name},
        )
      model_hint = ""
      max_tokens = None
      if persona_details:
        prompt_val = persona_details.get("prompt")
        if prompt_val:
          role = str(prompt_val)
        model_val = persona_details.get("model")
        if model_val:
          model_hint = str(model_val)
        tokens_val = persona_details.get("tokens")
        if isinstance(tokens_val, str):
          try:
            tokens_val = int(tokens_val)
          except ValueError:
            tokens_val = None
        if isinstance(tokens_val, int) and tokens_val > 0:
          max_tokens = tokens_val
      generator = getattr(openai, "generate_chat", None)
      fetch_chat = getattr(openai, "fetch_chat", None)
      response = None
      try:
        if generator:
          response = await generator(
            system_prompt=role,
            user_prompt=summary["raw_text_blob"],
            model=model_hint or None,
            max_tokens=max_tokens,
            persona=persona_name,
            persona_details=persona_details,
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            input_log=str(hours),
            token_count=summary["token_count_estimate"],
          )
        elif fetch_chat:
          response = await fetch_chat(
            [],
            role,
            summary["raw_text_blob"],
            max_tokens,
            persona=persona_name,
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            input_log=str(hours),
            token_count=summary["token_count_estimate"],
            model=model_hint or "gpt-4o-mini",
          )
      except Exception:
        logging.exception("[DiscordChatModule] chat generation failed")
        response = None
      if response is not None:
        if isinstance(response, dict):
          summary_text = response.get("content", "")
          model = response.get("model", model_hint or "")
          response_role = response.get("role", "")
        else:
          summary_text = getattr(response, "content", "")
          model = getattr(response, "model", model_hint or "")
          response_role = getattr(response, "role", "")
        if not role:
          role = response_role
    elapsed = time.perf_counter() - start
    logging.info(
      "[DiscordChatModule] summarize_chat",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "hours": hours,
        "user_id": user_id,
        "messages_collected": summary["messages_collected"],
        "token_count_estimate": summary["token_count_estimate"],
        "model": model,
        "elapsed": elapsed,
      },
    )
    return {
      "token_count_estimate": summary["token_count_estimate"],
      "messages_collected": summary["messages_collected"],
      "cap_hit": summary["cap_hit"],
      "summary_text": summary_text,
      "model": model,
      "role": role,
    }

  async def summarize_and_deliver(
    self,
    guild_id: int,
    channel_id: int,
    hours: int,
    user_id: int | None,
  ) -> dict[str, Any]:
    if hours < 1 or hours > 336:
      raise ValueError("hours must be between 1 and 336")
    result = await self.summarize_chat(guild_id, channel_id, hours, user_id)
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
      ack_message = f"Summary queued for delivery to <@{user_id}>." if user_id else "Summary queued for delivery."

    try:
      ack = await self.deliver_summary(
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
        "[DiscordChatModule] summarize_and_deliver failed",
        extra={"guild_id": guild_id, "channel_id": channel_id, "user_id": user_id},
      )
      ack = {
        "success": False,
        "queue_id": None,
        "dm_enqueued": False,
        "channel_ack_enqueued": False,
        "reason": "delivery_failed",
        "ack_message": ack_message,
      }
    return {
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

  async def deliver_summary(
    self,
    *,
    guild_id: int,
    channel_id: int | None,
    user_id: int | None,
    summary_text: str | None,
    ack_message: str,
    success: bool,
    reason: str | None = None,
    messages_collected: int | None = None,
    token_count_estimate: int | None = None,
    cap_hit: bool | None = None,
  ) -> dict:
    if not self.discord:
      raise RuntimeError("Discord bot module is not available")
    await self.discord.on_ready()
    queue_id = str(uuid.uuid4())
    dm_enqueued = False
    channel_ack_enqueued = False
    if summary_text and user_id:
      await self.discord.queue_user_message(user_id, summary_text)
      dm_enqueued = True
    if ack_message and channel_id:
      await self.discord.queue_channel_message(channel_id, ack_message)
      channel_ack_enqueued = True
    overall_success = bool(success and dm_enqueued)
    payload = {
      "success": overall_success,
      "queue_id": queue_id,
      "summary_success": bool(success),
      "dm_enqueued": dm_enqueued,
      "channel_ack_enqueued": channel_ack_enqueued,
      "reason": reason,
      "ack_message": ack_message,
    }
    if messages_collected is not None:
      payload["messages_collected"] = messages_collected
    if token_count_estimate is not None:
      payload["token_count_estimate"] = token_count_estimate
    if cap_hit is not None:
      payload["cap_hit"] = cap_hit
    logging.info(
      "[DiscordChatModule] deliver_summary",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "queue_id": queue_id,
        "success": overall_success,
        "reason": reason,
        "dm_enqueued": dm_enqueued,
        "channel_ack_enqueued": channel_ack_enqueued,
      },
    )
    return payload

  async def get_persona(
    self,
    persona: str,
    *,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
  ) -> Dict[str, Any]:
    await self.on_ready()
    persona_name = (persona or "").strip()
    if not persona_name:
      return {
        "success": False,
        "reason": "missing_persona",
        "ack_message": "Persona chat is currently unavailable.",
      }
    openai = getattr(self.app.state, "openai", None)
    if not openai:
      logging.warning(
        "[DiscordChatModule] OpenAI module unavailable for get_persona",
        extra={
          "persona": persona_name,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      return {
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      }
    await openai.on_ready()
    try:
      persona_details = await openai.get_persona_definition(persona_name)
    except Exception:
      logging.exception(
        "[DiscordChatModule] failed to load persona",
        extra={
          "persona": persona_name,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      persona_details = None
    if not persona_details:
      return {
        "success": False,
        "reason": "persona_not_found",
        "ack_message": f"Persona '{persona_name}' was not found.",
      }
    model = persona_details.get("model")
    tokens = persona_details.get("tokens")
    if isinstance(tokens, str):
      try:
        tokens = int(tokens)
      except ValueError:
        tokens = None
    payload: Dict[str, Any] = {
      "success": True,
      "persona_details": persona_details,
      "model": model,
    }
    if tokens is not None:
      payload["max_tokens"] = tokens
    return payload

  async def get_conversation_history(
    self,
    persona: str,
    *,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
    limit: int = 5,
  ) -> Dict[str, Any]:
    await self.on_ready()
    persona_name = (persona or "").strip()
    if not persona_name:
      return {
        "success": False,
        "reason": "missing_persona",
        "ack_message": "Persona chat is currently unavailable.",
      }
    openai = getattr(self.app.state, "openai", None)
    if not openai:
      logging.warning(
        "[DiscordChatModule] OpenAI module unavailable for conversation history",
        extra={
          "persona": persona_name,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      return {
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      }
    await openai.on_ready()
    try:
      persona_details = await openai.get_persona_definition(persona_name)
    except Exception:
      logging.exception(
        "[DiscordChatModule] failed to load persona for history",
        extra={
          "persona": persona_name,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      persona_details = None
    personas_recid = persona_details.get("recid") if persona_details else None
    if personas_recid is None:
      return {
        "success": False,
        "reason": "persona_not_found",
        "ack_message": f"Persona '{persona_name}' was not found.",
      }
    try:
      conversation_history = await openai.get_recent_persona_conversation_history(
        personas_recid=personas_recid,
        lookback_days=30,
        limit=limit,
      )
    except Exception:
      logging.exception(
        "[DiscordChatModule] failed to load persona conversation history",
        extra={
          "persona": persona_name,
          "personas_recid": personas_recid,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      return {
        "success": False,
        "reason": "conversation_history_unavailable",
        "ack_message": "Failed to load previous persona conversation.",
      }
    return {
      "success": True,
      "conversation_history": conversation_history,
      "personas_recid": personas_recid,
      "models_recid": persona_details.get("models_recid") if persona_details else None,
    }

  async def get_channel_history(
    self,
    guild_id: int,
    channel_id: int,
    *,
    persona: str | None = None,
    user_id: int | None = None,
  ) -> Dict[str, Any]:
    await self.on_ready()
    try:
      history = await self.fetch_channel_history_backwards(
        guild_id,
        channel_id,
        hours=1,
        max_messages=200,
      )
    except Exception:
      logging.exception(
        "[DiscordChatModule] failed to fetch channel history",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "persona": persona,
          "user_id": user_id,
        },
      )
      return {
        "success": False,
        "reason": "channel_history_unavailable",
        "ack_message": "Failed to fetch messages. Please try again later.",
      }
    messages = history.get("messages") or []
    channel_history: List[Dict[str, Any]] = []
    for msg in messages:
      content = getattr(msg, "content", None)
      if not content:
        continue
      author = getattr(msg, "author", None)
      author_name = None
      if author is not None:
        author_name = (
          getattr(author, "display_name", None)
          or getattr(author, "name", None)
          or getattr(author, "id", None)
        )
      channel_history.append(
        {
          "author": str(author_name) if author_name is not None else "unknown",
          "content": str(content),
          "created_at": getattr(msg, "created_at", None),
        }
      )
    return {"success": True, "channel_history": channel_history}

  async def insert_conversation_input(
    self,
    persona: str,
    message: str,
    *,
    persona_details: Dict[str, Any] | None = None,
    conversation_history: List[Dict[str, Any]] | None = None,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
  ) -> Dict[str, Any]:
    await self.on_ready()
    persona_name = (persona or "").strip()
    message_text = (message or "").strip()
    if not persona_name or not message_text:
      return {
        "success": False,
        "reason": "invalid_persona_usage",
        "ack_message": "Usage: !persona <persona> <message>",
      }
    openai = getattr(self.app.state, "openai", None)
    if not openai:
      logging.warning(
        "[DiscordChatModule] OpenAI module unavailable for insert_conversation_input",
        extra={
          "persona": persona_name,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      return {
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      }
    await openai.on_ready()
    if not persona_details:
      persona_response = await self.get_persona(
        persona_name,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
      )
      if not persona_response.get("success"):
        return persona_response
      persona_details = persona_response.get("persona_details") or {}
    personas_recid = persona_details.get("recid")
    models_recid = persona_details.get("models_recid")
    if personas_recid is None or models_recid is None:
      logging.warning(
        "[DiscordChatModule] persona missing identifiers",
        extra={"persona": persona_name},
      )
      return {
        "success": False,
        "reason": "persona_not_configured",
        "ack_message": "Persona chat is currently unavailable.",
      }
    return {
      "success": True,
      "conversation_reference": None,
      "personas_recid": personas_recid,
      "models_recid": models_recid,
    }

  async def generate_persona_response(
    self,
    persona: str,
    message: str,
    *,
    persona_details: Dict[str, Any] | None = None,
    conversation_history: List[Dict[str, Any]] | None = None,
    channel_history: List[Dict[str, Any]] | None = None,
    stored_context: List[Dict[str, Any]] | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    conversation_reference: int | None = None,
    personas_recid: int | None = None,
    models_recid: int | None = None,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
  ) -> Dict[str, Any]:
    await self.on_ready()
    persona_name = (persona or "").strip()
    message_text = (message or "").strip()
    if not persona_name or not message_text:
      return {
        "success": False,
        "reason": "invalid_persona_usage",
        "ack_message": "Usage: !persona <persona> <message>",
      }
    openai = getattr(self.app.state, "openai", None)
    if not openai:
      logging.warning(
        "[DiscordChatModule] OpenAI module unavailable for generate_persona_response",
        extra={
          "persona": persona_name,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      return {
        "success": False,
        "reason": "persona_module_unavailable",
        "ack_message": "Persona chat is currently unavailable.",
      }
    await openai.on_ready()
    if not persona_details:
      persona_response = await self.get_persona(
        persona_name,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
      )
      if not persona_response.get("success"):
        return persona_response
      persona_details = persona_response.get("persona_details") or {}
      model = persona_response.get("model", model)
      max_tokens = persona_response.get("max_tokens", max_tokens)
    model_hint = model or persona_details.get("model")
    tokens_hint = max_tokens or persona_details.get("tokens")
    try:
      tokens_hint = int(tokens_hint) if tokens_hint is not None else None
    except (TypeError, ValueError):
      tokens_hint = None
    conversation_history = conversation_history or []
    channel_history = channel_history or []

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
    stored_context = stored_context or []
    if stored_context:
      stored_parts: List[str] = []
      for msg in stored_context[-15:]:
        r = msg.get("role") or "user"
        c = msg.get("content") or ""
        if c:
          stored_parts.append(f"{r}: {c}")
      stored_text = "\n".join(stored_parts)
      if stored_text:
        context_sections.append("Recent stored conversation context:\n" + stored_text)
    prompt_context = "\n\n".join(context_sections)
    logging.info(
      "[DiscordChatModule] context assembled for persona response",
      extra={
        "persona": persona_name,
        "guild_id": guild_id,
        "channel_id": channel_id,
        "conversation_history_count": len(conversation_history),
        "channel_history_count": len(channel_history),
        "stored_context_count": len(stored_context),
        "context_sections_count": len(context_sections),
        "prompt_context_length": len(prompt_context),
      },
    )

    system_prompt = persona_details.get("prompt") or ""

    try:
      response = await openai.generate_chat(
        system_prompt=system_prompt,
        user_prompt=message_text,
        model=model_hint,
        max_tokens=tokens_hint,
        prompt_context=prompt_context,
        persona=None,
        persona_details=None,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        input_log=message_text,
        token_count=None,
      )
    except Exception:
      logging.exception(
        "[DiscordChatModule] OpenAI request failed for persona response",
        extra={
          "persona": persona_name,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
      )
      return {
        "success": False,
        "reason": "persona_generation_failed",
        "ack_message": "Failed to generate a persona response. Please try again later.",
      }

    if isinstance(response, dict):
      content = response.get("content")
      model_used = response.get("model", model_hint)
      usage = response.get("usage")
    else:
      content = getattr(response, "content", None)
      model_used = getattr(response, "model", model_hint)
      usage = getattr(response, "usage", None)

    total_tokens = None
    if isinstance(usage, dict):
      total_tokens = usage.get("total_tokens")

    return {
      "success": True,
      "response": {"text": content or "", "model": model_used},
      "model": model_used,
      "usage": usage,
      "conversation_reference": conversation_reference,
      "personas_recid": personas_recid,
      "models_recid": models_recid,
    }

  async def deliver_persona_response(
    self,
    *,
    persona: str,
    response: Dict[str, Any] | str | None,
    conversation_reference: int | None = None,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
  ) -> Dict[str, Any]:
    await self.on_ready()
    if not self.discord:
      raise RuntimeError("Discord bot module is not available")
    await self.discord.on_ready()
    if isinstance(response, str):
      response_text = response
    else:
      response_text = (response or {}).get("text") if isinstance(response, dict) else getattr(response, "text", "")
      if not response_text and isinstance(response, dict):
        response_text = response.get("content") or ""
    success = False
    try:
      if channel_id is not None and response_text:
        await self.discord.queue_channel_message(int(channel_id), response_text)
        success = True
    except Exception:
      logging.exception(
        "[DiscordChatModule] failed to queue persona response",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "persona": persona,
        },
      )
      success = False
    if success and user_id is not None:
      ack_message = f"Persona response queued for <@{user_id}>."
    elif success:
      ack_message = "Persona response queued."
    else:
      ack_message = "Persona chat is currently unavailable."
    reason = "persona_response_queued" if success else "persona_delivery_failed"
    return {
      "success": success,
      "reason": reason,
      "ack_message": ack_message,
      "conversation_reference": conversation_reference,
    }

  async def handle_persona_command(
    self,
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    command_text: str,
  ) -> dict:
    await self.on_ready()
    metadata = {
      "guild_id": guild_id,
      "channel_id": channel_id,
      "user_id": user_id,
    }
    context = await self._persona_parse_and_dispatch(command_text, metadata)
    if not context.get("success", True):
      await self._bump_channel_activity(metadata)
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_fetch_persona(context, metadata)
    if not context.get("success", True):
      await self._bump_channel_activity(metadata)
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_fetch_conversation(context, metadata)
    if not context.get("success", True):
      await self._bump_channel_activity(metadata)
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_fetch_channel_history(context, metadata)
    if not context.get("success", True):
      await self._bump_channel_activity(metadata)
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_insert_conversation_input(context, metadata)
    if not context.get("success", True):
      await self._bump_channel_activity(metadata)
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_generate_response(context, metadata)
    if not context.get("success", True):
      await self._bump_channel_activity(metadata)
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_deliver_response(context, metadata)
    await self._bump_channel_activity(metadata)
    return self._finalize_persona_context(context, success=context.get("success", True))

  async def _persona_parse_and_dispatch(self, command_text: str, metadata: dict) -> dict:
    try:
      persona, message = self._split_persona_command(command_text)
    except ValueError:
      return {
        "success": False,
        "reason": "invalid_persona_usage",
        "ack_message": "Usage: !persona <persona> <message>",
      }
    context = {
      "persona": persona,
      "message": message,
      "model": None,
      "max_tokens": None,
      "conversation": [],
      "response": None,
      "success": True,
    }
    return context

  async def _persona_fetch_persona(self, context: dict, metadata: dict) -> dict:
    response = await self.get_persona(
      context.get("persona"),
      guild_id=metadata.get("guild_id"),
      channel_id=metadata.get("channel_id"),
      user_id=metadata.get("user_id"),
    )
    context["persona_details"] = response.get("persona_details")
    context["model"] = response.get("model", context.get("model"))
    context["max_tokens"] = response.get("max_tokens", context.get("max_tokens"))
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  async def _persona_fetch_conversation(self, context: dict, metadata: dict) -> dict:
    context["conversation_history"] = []
    openai = getattr(self.app.state, "openai", None)
    if openai and metadata.get("guild_id") and metadata.get("channel_id"):
      try:
        stored_context = await openai.get_channel_context(
          metadata["guild_id"],
          metadata["channel_id"],
          limit=20,
        )
        if stored_context:
          context["stored_channel_context"] = stored_context
      except Exception:
        logging.exception("[DiscordChatModule] failed to fetch stored channel context")
    return context

  async def _persona_fetch_channel_history(self, context: dict, metadata: dict) -> dict:
    response = await self.get_channel_history(
      metadata.get("guild_id"),
      metadata.get("channel_id"),
      persona=context.get("persona"),
      user_id=metadata.get("user_id"),
    )
    context["channel_history"] = response.get("channel_history") or []
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  async def _persona_insert_conversation_input(self, context: dict, metadata: dict) -> dict:
    response = await self.insert_conversation_input(
      context.get("persona"),
      context.get("message"),
      persona_details=context.get("persona_details"),
      conversation_history=context.get("conversation_history", []),
      guild_id=metadata.get("guild_id"),
      channel_id=metadata.get("channel_id"),
      user_id=metadata.get("user_id"),
    )
    context["conversation_reference"] = response.get("conversation_reference")
    if response.get("personas_recid") is not None:
      context["personas_recid"] = response.get("personas_recid")
    if response.get("models_recid") is not None:
      context["models_recid"] = response.get("models_recid")
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    thread_id = self._generate_thread_id(
      metadata.get("guild_id"),
      metadata.get("channel_id"),
    )
    context["thread_id"] = thread_id

    openai = getattr(self.app.state, "openai", None)
    if openai and context.get("personas_recid") and context.get("models_recid"):
      await openai.log_message(
        personas_recid=context["personas_recid"],
        models_recid=context["models_recid"],
        role="user",
        content=context.get("message", ""),
        guild_id=metadata.get("guild_id"),
        channel_id=metadata.get("channel_id"),
        user_id=metadata.get("user_id"),
        thread_id=thread_id,
      )
    return context

  async def _persona_generate_response(self, context: dict, metadata: dict) -> dict:
    response = await self.generate_persona_response(
      context.get("persona"),
      context.get("message"),
      persona_details=context.get("persona_details"),
      conversation_history=context.get("conversation_history", []),
      channel_history=context.get("channel_history", []),
      stored_context=context.get("stored_channel_context", []),
      model=context.get("model"),
      max_tokens=context.get("max_tokens"),
      conversation_reference=context.get("conversation_reference"),
      personas_recid=context.get("personas_recid"),
      models_recid=context.get("models_recid"),
      guild_id=metadata.get("guild_id"),
      channel_id=metadata.get("channel_id"),
      user_id=metadata.get("user_id"),
    )
    context["response"] = response.get("response", context.get("response"))
    context["model"] = response.get("model", context.get("model"))
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")

    openai = getattr(self.app.state, "openai", None)
    if context.get("success") and context.get("thread_id"):
      response_text = ""
      resp = context.get("response")
      if isinstance(resp, dict):
        response_text = resp.get("text") or resp.get("content") or ""
      elif isinstance(resp, str):
        response_text = resp
      if response_text and openai:
        await openai.log_message(
          personas_recid=context.get("personas_recid", 0),
          models_recid=context.get("models_recid", 0),
          role="assistant",
          content=response_text,
          guild_id=metadata.get("guild_id"),
          channel_id=metadata.get("channel_id"),
          user_id=metadata.get("user_id"),
          thread_id=context["thread_id"],
        )
    return context

  async def _persona_deliver_response(self, context: dict, metadata: dict) -> dict:
    response = await self.deliver_persona_response(
      persona=context.get("persona"),
      response=context.get("response"),
      conversation_reference=context.get("conversation_reference"),
      guild_id=metadata.get("guild_id"),
      channel_id=metadata.get("channel_id"),
      user_id=metadata.get("user_id"),
    )
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  def _finalize_persona_context(self, context: dict, *, success: bool) -> dict:
    context = dict(context)
    context.setdefault("success", success)
    if context.get("success"):
      context.setdefault("ack_message", "Persona response queued.")
      context.setdefault("reason", "persona_response_queued")
    else:
      context.setdefault("ack_message", "Persona chat is currently unavailable.")
      context.setdefault("reason", context.get("reason") or "persona_failed")
    return context

  def _split_persona_command(self, command_text: str) -> tuple[str, str]:
    if not command_text or not command_text.strip():
      raise ValueError("empty persona command")
    parts = command_text.strip().split(None, 1)
    if len(parts) < 2:
      raise ValueError("persona command missing message")
    persona = parts[0].strip()
    message = parts[1].strip()
    if not persona or not message:
      raise ValueError("persona command requires persona and message")
    return persona, message
