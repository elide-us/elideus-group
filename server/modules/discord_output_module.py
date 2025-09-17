"""Discord output module responsible for delivering messages safely."""

import asyncio, logging, discord
from collections.abc import Awaitable, Callable
from typing import List, TYPE_CHECKING
from fastapi import FastAPI
from discord.ext import commands

from . import BaseModule

if TYPE_CHECKING:  # pragma: no cover
  from .discord_module import DiscordModule

_SendCallable = Callable[[str], Awaitable[None]]


class DiscordOutputModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: "DiscordModule" | None = None
    self._message_size_limit = 1998
    self._trickle_delay = 1.0
    self._send_lock = asyncio.Lock()

  async def startup(self):
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
    self.app.state.discord_output = self
    logging.info("[DiscordOutputModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    logging.info("[DiscordOutputModule] shutdown")
    if getattr(self.app.state, "discord_output", None) is self:
      self.app.state.discord_output = None
    self.discord = None

  def configure_message_window(self, max_message_size: int) -> None:
    if max_message_size <= 0:
      raise ValueError("max_message_size must be greater than zero")
    self._message_size_limit = max_message_size

  def configure_trickle_rate(self, delay_seconds: float) -> None:
    if delay_seconds < 0:
      raise ValueError("delay_seconds cannot be negative")
    self._trickle_delay = delay_seconds

  async def send_to_channel(self, channel_id: int, message: str) -> None:
    if not message:
      return
    channel = await self._resolve_channel(channel_id)
    await self._deliver_in_chunks(channel.send, message)

  async def send_to_user(self, user_id: int, message: str) -> None:
    if not message:
      return
    user = await self._resolve_user(user_id)
    await self._deliver_in_chunks(user.send, message)

  async def _resolve_channel(self, channel_id: int) -> discord.abc.Messageable:
    bot = self._get_bot()
    channel = bot.get_channel(channel_id)
    if channel is None:
      try:
        channel = await bot.fetch_channel(channel_id)
      except discord.DiscordException:
        logging.exception("[DiscordOutputModule] failed to fetch channel", extra={"channel_id": channel_id})
        raise
    if not hasattr(channel, "send"):
      raise RuntimeError(f"Channel {channel_id} is not send-capable")
    return channel

  async def _resolve_user(self, user_id: int) -> discord.abc.Messageable:
    bot = self._get_bot()
    user = bot.get_user(user_id)
    if user is None:
      try:
        user = await bot.fetch_user(user_id)
      except discord.DiscordException:
        logging.exception("[DiscordOutputModule] failed to fetch user", extra={"user_id": user_id})
        raise
    if not hasattr(user, "send"):
      raise RuntimeError(f"User {user_id} cannot receive messages")
    return user

  def _get_bot(self) -> commands.Bot:
    if not self.discord or not self.discord.bot:
      raise RuntimeError("Discord bot is not available")
    return self.discord.bot

  async def _deliver_in_chunks(self, sender: _SendCallable, text: str) -> None:
    chunks = self._yield_chunks(text, self._message_size_limit)
    async with self._send_lock:
      for chunk in chunks:
        await sender(chunk)
        if self._trickle_delay > 0:
          await asyncio.sleep(self._trickle_delay)

  @staticmethod
  def _wrap_line(line: str, max_message_size: int) -> List[str]:
    remaining = line
    parts: List[str] = []
    while remaining:
      if len(remaining) <= max_message_size:
        parts.append(remaining)
        break
      window = remaining[:max_message_size]
      split = window.rfind(" ")
      if split <= 0:
        split = max_message_size
      parts.append(remaining[:split])
      remaining = remaining[split:]
    if not parts:
      parts.append("")
    return parts

  @classmethod
  def _yield_chunks(cls, text: str, max_message_size: int) -> List[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    chunks: List[str] = []
    buffer = ""
    for raw_line in lines:
      line = raw_line
      if not line.strip() and not buffer.strip():
        continue
      wrapped = cls._wrap_line(line, max_message_size)
      for segment in wrapped[:-1]:
        candidate = segment if not buffer else buffer + "\n" + segment
        if candidate.strip() and candidate.strip() != "---":
          chunks.append(candidate)
        buffer = ""
      last_segment = wrapped[-1]
      candidate = last_segment if not buffer else buffer + ("\n" + last_segment if last_segment else "\n")
      if len(candidate) <= max_message_size:
        buffer = candidate
      else:
        if buffer.strip() and buffer.strip() != "---":
          chunks.append(buffer)
        buffer = last_segment
    if buffer.strip() and buffer.strip() != "---":
      chunks.append(buffer)
    return chunks
