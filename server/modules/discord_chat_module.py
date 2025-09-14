"""Discord chat utilities module."""

import logging, time, discord
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from typing import List, Any

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

  async def summarize_persona(self, text: str) -> List[str]:
    openai = getattr(self.app.state, "openai", None)
    if not openai or not getattr(openai, "client", None):
      return ["[[STUB: Persona summary output here]]"]
    await openai.on_ready()
    msg = await openai.fetch_chat(
      [],
      "Summarize the following conversation into bullet points.",
      text,
      300,
    )
    content = getattr(
      msg,
      "content",
      msg.get("content", "") if isinstance(msg, dict) else "",
    )
    return [line.strip() for line in content.splitlines() if line.strip()]

  async def uwu_persona(self, summary: List[str], user_id: int, user_message: str) -> str:
    openai = getattr(self.app.state, "openai", None)
    if not openai or not getattr(openai, "client", None):
      return "[[STUB: uwu persona output here]]"
    await openai.on_ready()
    prompt_context = "\n".join(summary)
    role = f"You are a playful catgirl assistant responding to user {user_id} in uwu style."
    msg = await openai.fetch_chat([], role, user_message, 120, prompt_context)
    return getattr(
      msg,
      "content",
      msg.get("content", "") if isinstance(msg, dict) else "",
    )

  async def log_conversation(
    self,
    persona: str,
    guild_id: int,
    channel_id: int,
    input_data: str,
    output_data: str,
  ):
    if not self.db:
      return
    try:
      res = await self.db.run(
        "db:assistant:personas:get_by_name:1",
        {"name": persona},
      )
      recid = res.rows[0]["recid"] if res.rows else None
      if recid is not None:
        await self.db.run(
          "db:assistant:conversations:insert:1",
          {
            "personas_recid": recid,
            "guild_id": str(guild_id),
            "channel_id": str(channel_id),
            "input_data": input_data,
            "output_data": output_data,
          },
        )
    except Exception:
      logging.exception("[DiscordChatModule] log_conversation failed")

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

  async def uwu_chat(
    self,
    guild_id: int,
    channel_id: int,
    user_id: int,
    message: str,
    hours: int = 1,
    max_messages: int = 12,
  ) -> dict:
    hours = max(hours, 1)
    max_messages = max(max_messages, 12)
    start = time.perf_counter()
    summary = await self.summarize_channel(guild_id, channel_id, hours, max_messages)
    summary_lines = await self.summarize_persona(summary["raw_text_blob"])
    uwu_response = await self.uwu_persona(summary_lines, user_id, message)
    elapsed = time.perf_counter() - start
    logging.info(
      "[DiscordChatModule] uwu_chat",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "hours": hours,
        "messages_collected": summary["messages_collected"],
        "token_count_estimate": summary["token_count_estimate"],
        "input_length": len(message),
        "elapsed": elapsed,
      },
    )
    return {
      "token_count_estimate": summary["token_count_estimate"],
      "summary_lines": summary_lines,
      "uwu_response_text": uwu_response,
    }
