"""Discord input provider that registers commands and dispatches workflows."""

from __future__ import annotations

import json, logging, time
from typing import TYPE_CHECKING

from fastapi import Request
from discord.ext import commands

from . import SocialInputProvider

if TYPE_CHECKING:  # pragma: no cover
  from ...discord_bot_module import DiscordBotModule
  from ...discord_output_module import DiscordOutputModule
  from ...social_input_module import SocialInputModule
  from discord.ext.commands import Bot


class DiscordInputProvider(SocialInputProvider):
  name = "discord"

  def __init__(self, module: "SocialInputModule", discord: "DiscordBotModule"):
    super().__init__(module)
    self.discord = discord
    self.bot: "Bot" | None = None
    self._registered: dict[str, commands.Command] = {}

  async def startup(self):
    await self.discord.on_ready()
    if not self.discord.bot:
      raise RuntimeError("Discord bot is not initialized")
    self.bot = self.discord.bot
    self._register_commands()
    self.discord.register_input_provider(self)

  async def shutdown(self):
    if self.bot:
      for name in list(self._registered.keys()):
        self.bot.remove_command(name)
      self._registered.clear()
    self.bot = None

  def _register_commands(self) -> None:
    assert self.bot
    for name in list(self._registered.keys()):
      self.bot.remove_command(name)
    @commands.command(name="rpc")
    async def rpc_command(ctx, *, op: str):
      await self._handle_rpc_command(ctx, op=op)

    @commands.command(name="summarize")
    async def summarize_command(ctx, hours: str):
      await self._handle_summarize_command(ctx, hours)

    self.bot.add_command(rpc_command)
    self.bot.add_command(summarize_command)
    self._registered = {"rpc": rpc_command, "summarize": summarize_command}

  async def _handle_rpc_command(self, ctx, *, op: str):
    from rpc.handler import handle_rpc_request

    start = time.perf_counter()
    guild_id = getattr(ctx.guild, "id", 0)
    user_id = getattr(ctx.author, "id", 0)
    if guild_id and user_id:
      self.discord.bump_rate_limits(guild_id, user_id)
    body = json.dumps({"op": op}).encode()

    async def receive():
      nonlocal body
      data = body
      body = b""
      return {"type": "http.request", "body": data, "more_body": False}

    scope = {
      "type": "http",
      "method": "POST",
      "path": "/rpc",
      "headers": [(b"content-type", b"application/json")],
      "app": self.discord.app,
    }
    req = Request(scope, receive)
    req.state.discord_ctx = ctx

    try:
      resp = await handle_rpc_request(req)
      payload = resp.payload
      if hasattr(payload, "model_dump"):
        data = json.dumps(payload.model_dump())
      else:
        data = str(payload)
      await self._send_channel(ctx.channel.id, data)
      elapsed = time.perf_counter() - start
      logging.info(
        "[DiscordInputProvider] rpc",
        extra={
          "guild_id": guild_id,
          "channel_id": ctx.channel.id,
          "user_id": user_id,
          "op": op,
          "elapsed": elapsed,
        },
      )
    except Exception as exc:
      elapsed = time.perf_counter() - start
      logging.exception(
        "[DiscordInputProvider] rpc failed",
        extra={
          "guild_id": guild_id,
          "channel_id": getattr(ctx.channel, "id", 0),
          "user_id": user_id,
          "op": op,
          "elapsed": elapsed,
        },
      )
      await self._send_channel(ctx.channel.id, f"Error: {exc}")

  async def _handle_summarize_command(self, ctx, hours: str):
    from rpc.handler import handle_rpc_request

    start = time.perf_counter()
    guild_id = getattr(ctx.guild, "id", 0)
    user_id = getattr(ctx.author, "id", 0)
    if guild_id and user_id:
      self.discord.bump_rate_limits(guild_id, user_id)

    try:
      hrs = int(hours)
    except ValueError:
      await self._send_channel(ctx.channel.id, "Usage: !summarize <hours>")
      return
    if hrs < 1 or hrs > 336:
      await self._send_channel(ctx.channel.id, "Hours must be between 1 and 336")
      return

    body = json.dumps({
      "op": "urn:discord:chat:summarize_channel:1",
      "payload": {
        "guild_id": guild_id,
        "channel_id": getattr(ctx.channel, "id", 0),
        "hours": hrs,
        "user_id": user_id,
      },
    }).encode()

    async def receive():
      nonlocal body
      data = body
      body = b""
      return {"type": "http.request", "body": data, "more_body": False}

    scope = {
      "type": "http",
      "method": "POST",
      "path": "/rpc",
      "headers": [(b"content-type", b"application/json")],
      "app": self.discord.app,
    }
    req = Request(scope, receive)
    req.state.discord_ctx = ctx

    try:
      resp = await handle_rpc_request(req)
      payload = resp.payload
      if hasattr(payload, "model_dump"):
        data = payload.model_dump()
      elif isinstance(payload, dict):
        data = payload
      else:
        data = {"summary": str(payload)}
      if not data.get("messages_collected"):
        await self._send_channel(ctx.channel.id, "No messages found in the specified time range")
        return
      if data.get("cap_hit"):
        await self._send_channel(ctx.channel.id, "Channel too active to summarize; message cap hit")
        return
      summary_text = data.get("summary") or json.dumps(data)
      try:
        openai = getattr(self.discord.app.state, "openai", None)
        output: "DiscordOutputModule" | None = getattr(self.discord, "output_module", None)
        if not output:
          output = self.discord._get_output_module()
        if openai and getattr(openai, "summary_queue", None) and output:
          await openai.summary_queue.add(output.send_to_user, user_id, summary_text)
        else:
          await self.discord.send_user_message(user_id, summary_text)
      except Exception:
        logging.exception("[DiscordInputProvider] summarize delivery failed")
        await self._send_channel(ctx.channel.id, "Failed to send summary. Please try again later.")
        return
      elapsed = time.perf_counter() - start
      logging.info(
        "[DiscordInputProvider] summarize",
        extra={
          "guild_id": guild_id,
          "channel_id": getattr(ctx.channel, "id", 0),
          "user_id": user_id,
          "hours": hrs,
          "token_count_estimate": data.get("token_count_estimate"),
          "messages_collected": data.get("messages_collected"),
          "cap_hit": data.get("cap_hit"),
          "model": data.get("model"),
          "role": data.get("role"),
          "elapsed": elapsed,
        },
      )
      logging.debug("[DiscordInputProvider] summarize response", extra=data)
    except Exception:
      elapsed = time.perf_counter() - start
      logging.exception(
        "[DiscordInputProvider] summarize failed",
        extra={
          "guild_id": guild_id,
          "channel_id": getattr(ctx.channel, "id", 0),
          "user_id": user_id,
          "hours": hrs,
          "elapsed": elapsed,
        },
      )
      await self._send_channel(ctx.channel.id, "Failed to fetch messages. Please try again later.")

  async def _send_channel(self, channel_id: int, message: str) -> None:
    try:
      await self.discord.send_channel_message(channel_id, message)
    except Exception:
      logging.exception(
        "[DiscordInputProvider] failed to send channel message",
        extra={"channel_id": channel_id},
      )

