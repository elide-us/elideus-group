"""Discord chat utilities module."""

import logging, time, discord
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

  async def get_persona_instructions(self, persona_name: str) -> str:
    openai = getattr(self.app.state, "openai", None)
    if not openai:
      return ""
    try:
      await openai.on_ready()
      definition = await openai.get_persona_definition(persona_name)
    except Exception:
      logging.exception("[DiscordChatModule] failed to fetch persona instructions", extra={"persona": persona_name})
      return ""
    if not definition:
      return ""
    return str(definition.get("prompt", ""))

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
    summary_text = "[[STUB: summarize persona output here]]"
    model = ""
    role = ""
    if openai and getattr(openai, "client", None):
      await openai.on_ready()
      role = await self.get_persona_instructions("summarize")
      response = None
      generator = getattr(openai, "generate_chat", None)
      if generator:
        response = await generator(
          system_prompt=role,
          user_prompt=summary["raw_text_blob"],
          persona="summarize",
          guild_id=guild_id,
          channel_id=channel_id,
          user_id=user_id,
          input_log=str(hours),
          token_count=summary["token_count_estimate"],
        )
      else:
        fetch_chat = getattr(openai, "fetch_chat", None)
        if fetch_chat:
          response = await fetch_chat(
            [],
            role,
            summary["raw_text_blob"],
            None,
            persona="summarize",
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            input_log=str(hours),
            token_count=summary["token_count_estimate"],
          )
      if response is not None:
        if isinstance(response, dict):
          summary_text = response.get("content", "")
          model = response.get("model", "")
        else:
          summary_text = getattr(response, "content", "")
          model = getattr(response, "model", "")
      persona_details = None
      try:
        persona_details = await openai.get_persona_definition("summarize")
      except Exception:
        logging.exception("[DiscordChatModule] failed to load summarize persona")
      role = persona_details.get("prompt", "") if persona_details else ""
      model_hint = persona_details.get("model") if persona_details else ""
      max_tokens = persona_details.get("tokens") if persona_details else None
      persona_recid = persona_details.get("recid") if persona_details else None
      models_recid = persona_details.get("models_recid") if persona_details else None
      msg = await openai.submit_chat_prompt(
        system_prompt=role,
        model=model_hint or "gpt-4o-mini",
        max_tokens=max_tokens,
        user_prompt=summary["raw_text_blob"],
        persona_name="summarize",
        persona_recid=persona_recid,
        models_recid=models_recid,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        input_log=str(hours),
        token_count=summary["token_count_estimate"],
      )
      summary_text = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
      model = msg.get("model", model_hint or "") if isinstance(msg, dict) else getattr(msg, "model", model_hint or "")
      if not role:
        role = msg.get("role", "") if isinstance(msg, dict) else getattr(msg, "role", "")
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
