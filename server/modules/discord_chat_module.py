"""Discord chat utilities module."""

import logging, time, discord, uuid
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from typing import List

from . import BaseModule
from .discord_bot_module import DiscordBotModule


class DiscordChatModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordBotModule | None = None

  async def startup(self):
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    self.app.state.discord_chat = self
    logging.info("[DiscordChatModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    logging.info("[DiscordChatModule] shutdown")

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
    output = self.discord._require_output_module()
    queue_id = str(uuid.uuid4())
    dm_enqueued = False
    channel_ack_enqueued = False
    if summary_text and user_id:
      await output.queue_user_message(user_id, summary_text)
      dm_enqueued = True
    if ack_message and channel_id:
      await output.queue_channel_message(channel_id, ack_message)
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
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_fetch_persona(context, metadata)
    if not context.get("success", True):
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_fetch_conversation(context, metadata)
    if not context.get("success", True):
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_fetch_channel_history(context, metadata)
    if not context.get("success", True):
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_insert_conversation_input(context, metadata)
    if not context.get("success", True):
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_generate_response(context, metadata)
    if not context.get("success", True):
      return self._finalize_persona_context(context, success=False)
    context = await self._persona_deliver_response(context, metadata)
    return self._finalize_persona_context(context, success=context.get("success", True))

  async def _persona_parse_and_dispatch(self, command_text: str, metadata: dict) -> dict:
    persona, message = self._split_persona_command(command_text)
    payload = {
      "persona": persona,
      "message": message,
      "guild_id": metadata.get("guild_id"),
      "channel_id": metadata.get("channel_id"),
      "user_id": metadata.get("user_id"),
      "model": None,
      "max_tokens": None,
      "conversation": [],
      "response": None,
    }
    response = await self._dispatch_persona_rpc(
      "urn:discord:chat:persona_command:1",
      payload,
      metadata,
    )
    context = {
      "persona": persona,
      "message": message,
      "model": response.get("model"),
      "max_tokens": response.get("max_tokens"),
      "conversation": response.get("conversation") or [],
      "response": response.get("response"),
      "success": response.get("success", True),
      "reason": response.get("reason"),
      "ack_message": response.get("ack_message"),
    }
    context.update({k: v for k, v in response.items() if k not in context})
    return context

  async def _persona_fetch_persona(self, context: dict, metadata: dict) -> dict:
    payload = {
      "persona": context.get("persona"),
      "guild_id": metadata.get("guild_id"),
      "channel_id": metadata.get("channel_id"),
      "user_id": metadata.get("user_id"),
    }
    response = await self._dispatch_persona_rpc(
      "urn:discord:chat:get_persona:1",
      payload,
      metadata,
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
    payload = {
      "persona": context.get("persona"),
      "guild_id": metadata.get("guild_id"),
      "channel_id": metadata.get("channel_id"),
      "user_id": metadata.get("user_id"),
      "limit": 20,
    }
    response = await self._dispatch_persona_rpc(
      "urn:discord:chat:get_conversation_history:1",
      payload,
      metadata,
    )
    context["conversation_history"] = response.get("conversation_history") or []
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  async def _persona_fetch_channel_history(self, context: dict, metadata: dict) -> dict:
    payload = {
      "channel_id": metadata.get("channel_id"),
      "guild_id": metadata.get("guild_id"),
      "user_id": metadata.get("user_id"),
      "persona": context.get("persona"),
    }
    response = await self._dispatch_persona_rpc(
      "urn:discord:chat:get_channel_history:1",
      payload,
      metadata,
    )
    context["channel_history"] = response.get("channel_history") or []
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  async def _persona_insert_conversation_input(self, context: dict, metadata: dict) -> dict:
    payload = {
      "persona": context.get("persona"),
      "message": context.get("message"),
      "conversation_history": context.get("conversation_history", []),
      "guild_id": metadata.get("guild_id"),
      "channel_id": metadata.get("channel_id"),
      "user_id": metadata.get("user_id"),
    }
    response = await self._dispatch_persona_rpc(
      "urn:discord:chat:insert_conversation_input:1",
      payload,
      metadata,
    )
    context["conversation_reference"] = response.get("conversation_reference")
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  async def _persona_generate_response(self, context: dict, metadata: dict) -> dict:
    payload = {
      "persona": context.get("persona"),
      "message": context.get("message"),
      "persona_details": context.get("persona_details"),
      "conversation_history": context.get("conversation_history", []),
      "channel_history": context.get("channel_history", []),
      "model": context.get("model"),
      "max_tokens": context.get("max_tokens"),
      "guild_id": metadata.get("guild_id"),
      "channel_id": metadata.get("channel_id"),
      "user_id": metadata.get("user_id"),
    }
    response = await self._dispatch_persona_rpc(
      "urn:discord:chat:generate_persona_response:1",
      payload,
      metadata,
    )
    context["response"] = response.get("response", context.get("response"))
    context["model"] = response.get("model", context.get("model"))
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  async def _persona_deliver_response(self, context: dict, metadata: dict) -> dict:
    payload = {
      "persona": context.get("persona"),
      "response": context.get("response"),
      "model": context.get("model"),
      "guild_id": metadata.get("guild_id"),
      "channel_id": metadata.get("channel_id"),
      "user_id": metadata.get("user_id"),
    }
    response = await self._dispatch_persona_rpc(
      "urn:discord:chat:deliver_persona_response:1",
      payload,
      metadata,
    )
    context["success"] = response.get("success", True)
    context["reason"] = response.get("reason", context.get("reason"))
    if response.get("ack_message"):
      context["ack_message"] = response.get("ack_message")
    return context

  async def _dispatch_persona_rpc(self, op: str, payload: dict, metadata: dict) -> dict:
    from rpc.handler import dispatch_rpc_op

    try:
      response = await dispatch_rpc_op(
        self.app,
        op,
        payload,
        discord_ctx=metadata,
      )
    except Exception:
      logging.exception(
        "[DiscordChatModule] persona RPC dispatch failed",
        extra={"op": op, "guild_id": metadata.get("guild_id"), "channel_id": metadata.get("channel_id"), "user_id": metadata.get("user_id")},
      )
      return {
        "success": False,
        "reason": "persona_rpc_failure",
        "ack_message": "Persona chat is currently unavailable.",
      }
    payload_obj = getattr(response, "payload", None)
    if hasattr(payload_obj, "model_dump"):
      return payload_obj.model_dump()
    if isinstance(payload_obj, dict):
      return dict(payload_obj)
    if payload_obj is None:
      return {"success": True}
    return {"success": True, "result": payload_obj}

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
