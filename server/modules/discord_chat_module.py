"""Discord chat utilities module."""

import logging, time, discord
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from typing import List

from . import BaseModule
from .discord_module import DiscordModule
from .db_module import DbModule


class DiscordChatModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordModule | None = None
    self.db: DbModule | None = None

  async def startup(self):
    self.discord = self.app.state.discord
    await self.discord.on_ready()
    self.db = self.app.state.db
    await self.db.on_ready()
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

  async def get_persona_instructions(self, name: str) -> str:
    if not self.db:
      return ""
    try:
      res = await self.db.run(
        "db:assistant:personas:get_by_name:1",
        {"name": name},
      )
      if res.rows:
        return res.rows[0].get("element_prompt") or ""
    except Exception:
      logging.exception("[DiscordChatModule] get_persona_instructions failed")
    return ""

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
    summary_text = "[[STUB: summarize persona output here]]"
    model = ""
    role = ""
    if openai and getattr(openai, "client", None):
      await openai.on_ready()
      role = await self.get_persona_instructions("summarize")
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
        response = await openai.fetch_chat(
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
      if isinstance(response, dict):
        summary_text = response.get("content", "")
        model = response.get("model", "")
      else:
        summary_text = getattr(response, "content", "")
        model = getattr(response, "model", "")
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
