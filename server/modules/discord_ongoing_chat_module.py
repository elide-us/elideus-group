"""Discord ongoing chat automation module."""

import asyncio, logging, random
from typing import List

from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule
from .discord_module import DiscordModule
from .discord_chat_module import DiscordChatModule
from .openai_module import OpenaiModule
from server.helpers.discord import send_to_discord


class DiscordOngoingChatModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.discord: DiscordModule | None = None
    self.discord_chat: DiscordChatModule | None = None
    self.openai: OpenaiModule | None = None
    self.interval_seconds = 300
    self.context_messages = 5
    self.history_hours = 1
    self.history_limit = 100
    self._task: asyncio.Task | None = None
    self._lock = asyncio.Lock()

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
    self.discord_chat = getattr(self.app.state, "discord_chat", None)
    if self.discord_chat:
      await self.discord_chat.on_ready()
    self.openai = getattr(self.app.state, "openai", None)
    if self.openai:
      await self.openai.on_ready()
    self.app.state.discord_ongoing_chat = self
    self._task = asyncio.create_task(self._loop())
    logging.info("[DiscordOngoingChatModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    if self._task:
      self._task.cancel()
      try:
        await self._task
      except asyncio.CancelledError:
        pass
      self._task = None
    self.db = None
    self.discord = None
    self.discord_chat = None
    self.openai = None
    logging.info("[DiscordOngoingChatModule] shutdown")

  async def _loop(self):
    try:
      while True:
        await asyncio.sleep(self.interval_seconds)
        try:
          await self._run_cycle()
        except asyncio.CancelledError:
          raise
        except Exception:
          logging.exception("[DiscordOngoingChatModule] cycle failed")
    except asyncio.CancelledError:
      raise

  async def _run_cycle(self):
    if self._lock.locked():
      logging.debug("[DiscordOngoingChatModule] cycle skipped: lock busy")
      return
    async with self._lock:
      await self._execute_cycle()

  async def _execute_cycle(self):
    if not self.db or not self.openai or not getattr(self.openai, "client", None):
      logging.debug("[DiscordOngoingChatModule] cycle skipped: OpenAI unavailable")
      return
    if not self.discord or not getattr(self.discord, "bot", None):
      logging.debug("[DiscordOngoingChatModule] cycle skipped: Discord bot unavailable")
      return
    if not self.discord_chat:
      logging.debug("[DiscordOngoingChatModule] cycle skipped: Discord chat module unavailable")
      return

    conversations = await self.db.run("db:assistant:conversations:list_recent:1", {})
    rows = list(conversations.rows or [])
    if not rows:
      logging.debug("[DiscordOngoingChatModule] cycle skipped: no conversation history")
      return

    guild_id = self._to_int(rows[0].get("element_guild_id"))
    channel_id = self._to_int(rows[0].get("element_channel_id"))
    if not guild_id or not channel_id:
      logging.debug("[DiscordOngoingChatModule] cycle skipped: missing guild/channel")
      return

    context_outputs = [
      (row.get("element_output") or "").strip()
      for row in reversed(rows)
      if (row.get("element_output") or "").strip()
    ]
    if len(context_outputs) > self.context_messages:
      context_outputs = context_outputs[-self.context_messages :]

    persona = await self._select_persona()
    if not persona:
      logging.debug("[DiscordOngoingChatModule] cycle skipped: no personas available")
      return
    persona_name = persona["name"]
    persona_prompt = persona["prompt"]

    history_lines = await self._collect_user_history(guild_id, channel_id)
    prompt_context = self._build_prompt_context(context_outputs, history_lines)

    token_estimate = None
    if prompt_context:
      try:
        token_estimate = self.discord_chat.estimate_tokens(prompt_context)
      except Exception:
        logging.exception("[DiscordOngoingChatModule] failed to estimate tokens")

    bot_user_id = None
    if getattr(self.discord.bot, "user", None):
      bot_user_id = self._to_int(getattr(self.discord.bot.user, "id", None))

    response = await self.openai.fetch_chat(
      [],
      persona_prompt,
      "Let's keep this conversation going...",
      None,
      prompt_context,
      persona=persona_name,
      guild_id=guild_id,
      channel_id=channel_id,
      user_id=bot_user_id,
      input_log="Let's keep this conversation going...",
      token_count=token_estimate,
    )

    response_text = self._extract_response_text(response)
    if not response_text:
      logging.debug("[DiscordOngoingChatModule] cycle skipped: empty response")
      return

    channel = self.discord.bot.get_channel(channel_id)
    if not channel:
      logging.warning(
        "[DiscordOngoingChatModule] channel not found",
        extra={"guild_id": guild_id, "channel_id": channel_id},
      )
      return

    await send_to_discord(channel, response_text)
    logging.info(
      "[DiscordOngoingChatModule] persona message sent",
      extra={
        "persona": persona_name,
        "guild_id": guild_id,
        "channel_id": channel_id,
        "context_messages": len(context_outputs),
        "history_lines": len(history_lines),
      },
    )

  async def _select_persona(self) -> dict | None:
    assert self.db
    res = await self.db.run("db:assistant:personas:list:1", {})
    personas = []
    for row in res.rows or []:
      name = (row.get("name") or "").strip()
      prompt = (row.get("prompt") or "").strip()
      if not name or not prompt:
        continue
      personas.append({"name": name, "prompt": prompt})
    if not personas:
      return None
    return random.choice(personas)

  async def _collect_user_history(self, guild_id: int, channel_id: int) -> List[str]:
    assert self.discord_chat
    try:
      history = await self.discord_chat.fetch_channel_history_backwards(
        guild_id,
        channel_id,
        self.history_hours,
        max_messages=self.history_limit,
      )
    except Exception:
      logging.exception("[DiscordOngoingChatModule] failed to collect history")
      return []
    lines: List[str] = []
    for message in history.get("messages", []) or []:
      author = getattr(message, "author", None)
      if author and getattr(author, "bot", False):
        continue
      content = (getattr(message, "content", None) or "").strip()
      if not content:
        continue
      name = (
        getattr(author, "display_name", None)
        or getattr(author, "name", None)
        or "User"
      )
      lines.append(f"{name}: {content}")
    return lines[-self.history_limit :]

  def _build_prompt_context(self, outputs: List[str], history_lines: List[str]) -> str:
    sections: List[str] = []
    if outputs:
      formatted = "\n".join(f"- {text}" for text in outputs)
      sections.append("Recent assistant responses:\n" + formatted)
    if history_lines:
      formatted = "\n".join(f"- {line}" for line in history_lines)
      sections.append("Recent user messages:\n" + formatted)
    return "\n\n".join(sections)

  def _extract_response_text(self, response) -> str:
    if hasattr(response, "content"):
      return getattr(response, "content") or ""
    if isinstance(response, dict):
      return response.get("content") or response.get("message", "")
    return str(response or "")

  def _to_int(self, value) -> int | None:
    try:
      if value is None:
        return None
      return int(value)
    except (TypeError, ValueError):
      return None
