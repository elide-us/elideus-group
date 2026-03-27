"""Discord input provider that registers commands and dispatches workflows."""

from __future__ import annotations

import logging, time
from typing import TYPE_CHECKING

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

    @commands.command(name="summarize")
    async def summarize_command(ctx, hours: str):
      await self._handle_summarize_command(ctx, hours)

    @commands.command(name="persona")
    async def persona_command(ctx, *, request: str | None = None):
      await self._handle_persona_command(ctx, request)

    @commands.command(name="credits")
    async def credits_command(ctx):
      await self._handle_credits_command(ctx)

    @commands.command(name="guildcredits")
    async def guildcredits_command(ctx):
      await self._handle_guildcredits_command(ctx)

    self.bot.add_command(summarize_command)
    self.bot.add_command(persona_command)
    self.bot.add_command(credits_command)
    self.bot.add_command(guildcredits_command)
    self._registered = {
      "summarize": summarize_command,
      "persona": persona_command,
      "credits": credits_command,
      "guildcredits": guildcredits_command,
    }

  async def _handle_summarize_command(self, ctx, hours: str):
    from rpc.handler import dispatch_rpc_op

    start = time.perf_counter()
    guild_id = getattr(ctx.guild, "id", 0)
    user_id = getattr(ctx.author, "id", 0)
    if guild_id and user_id:
      self.discord.bump_rate_limits(guild_id, user_id)

    try:
      hrs = int(hours)
    except ValueError:
      await self._queue_channel_notice(ctx, "Usage: !summarize <hours>", reason="invalid_hours")
      return
    if hrs < 1 or hrs > 336:
      await self._queue_channel_notice(ctx, "Hours must be between 1 and 336", reason="hours_out_of_range")
      return

    payload = {
      "guild_id": guild_id,
      "channel_id": getattr(ctx.channel, "id", 0),
      "hours": hrs,
      "user_id": user_id,
    }
    metadata = {
      "guild_id": guild_id,
      "channel_id": payload["channel_id"],
      "user_id": user_id,
    }

    try:
      resp = await dispatch_rpc_op(
        self.discord.app,
        "urn:discord:chat:summarize_channel:1",
        payload,
        discord_ctx=metadata,
      )
      payload = resp.payload
      if hasattr(payload, "model_dump"):
        data = payload.model_dump()
      elif isinstance(payload, dict):
        data = dict(payload)
      else:
        data = {"success": bool(payload)}
      if not data.get("success"):
        message = data.get("ack_message") or "Failed to send summary. Please try again later."
        await self._queue_channel_notice(ctx, message, reason=data.get("reason") or "delivery_failed")

      try:
        from queryregistry.discord.channels import bump_activity_request
        from queryregistry.discord.channels.models import BumpChannelActivityParams
        db = getattr(self.discord.app.state, "db", None)
        if db:
          await db.run(
            bump_activity_request(
              BumpChannelActivityParams(channel_id=str(getattr(ctx.channel, "id", 0)))
            )
          )
      except Exception:
        pass

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
          "queue_id": data.get("queue_id"),
          "dm_enqueued": data.get("dm_enqueued"),
          "channel_ack_enqueued": data.get("channel_ack_enqueued"),
          "reason": data.get("reason"),
          "elapsed": elapsed,
        },
      )
      logging.debug("[DiscordInputProvider] summarize response", extra=data)
      return
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
      await self._queue_channel_notice(ctx, "Failed to fetch messages. Please try again later.", reason="rpc_failure")

  async def _handle_credits_command(self, ctx):
    from rpc.handler import dispatch_rpc_op

    start = time.perf_counter()
    guild_id = getattr(ctx.guild, "id", 0)
    user_id = getattr(ctx.author, "id", 0)
    channel_id = getattr(ctx.channel, "id", 0)
    if guild_id and user_id:
      self.discord.bump_rate_limits(guild_id, user_id)
    metadata = {
      "guild_id": guild_id,
      "channel_id": channel_id,
      "user_id": user_id,
    }

    try:
      resp = await dispatch_rpc_op(
        self.discord.app,
        "urn:discord:command:get_credits:1",
        {"discord_id": str(user_id)},
        discord_ctx=metadata,
      )
      payload = resp.payload if isinstance(resp.payload, dict) else {}
      credits = payload.get("credits", 0)
      reserve = payload.get("reserve")
      message = f"Credits: {credits}"
      if reserve is not None:
        message += f" (reserve: {reserve})"
      await self._queue_channel_notice(ctx, message, reason="credits_command")
      elapsed = time.perf_counter() - start
      logging.info(
        "[DiscordInputProvider] credits",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "credits": credits,
          "reserve": reserve,
          "elapsed": elapsed,
        },
      )
    except Exception as exc:
      elapsed = time.perf_counter() - start
      logging.exception(
        "[DiscordInputProvider] credits failed",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "elapsed": elapsed,
        },
      )
      await self._queue_channel_notice(ctx, f"Error: {exc}", reason="credits_command_error")

  async def _handle_guildcredits_command(self, ctx):
    from rpc.handler import dispatch_rpc_op

    start = time.perf_counter()
    guild_id = getattr(ctx.guild, "id", 0)
    user_id = getattr(ctx.author, "id", 0)
    channel_id = getattr(ctx.channel, "id", 0)
    if guild_id and user_id:
      self.discord.bump_rate_limits(guild_id, user_id)
    metadata = {
      "guild_id": guild_id,
      "channel_id": channel_id,
      "user_id": user_id,
    }

    try:
      resp = await dispatch_rpc_op(
        self.discord.app,
        "urn:discord:command:get_guild_credits:1",
        {"guild_id": str(guild_id)},
        discord_ctx=metadata,
      )
      payload = resp.payload if isinstance(resp.payload, dict) else {}
      credits = payload.get("credits", 0)
      guild_value = payload.get("guild_id", str(guild_id))
      await self._queue_channel_notice(ctx, f"Guild {guild_value} credits: {credits}", reason="guildcredits_command")
      elapsed = time.perf_counter() - start
      logging.info(
        "[DiscordInputProvider] guildcredits",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "credits": credits,
          "elapsed": elapsed,
        },
      )
    except Exception as exc:
      elapsed = time.perf_counter() - start
      logging.exception(
        "[DiscordInputProvider] guildcredits failed",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "elapsed": elapsed,
        },
      )
      await self._queue_channel_notice(ctx, f"Error: {exc}", reason="guildcredits_command_error")

  async def _handle_persona_command(self, ctx, request: str | None):
    from rpc.handler import dispatch_rpc_op

    start = time.perf_counter()
    guild_id = getattr(ctx.guild, "id", 0)
    user_id = getattr(ctx.author, "id", 0)
    channel_id = getattr(ctx.channel, "id", 0)
    if guild_id and user_id:
      self.discord.bump_rate_limits(guild_id, user_id)
    if not request or not request.strip():
      await self._queue_channel_notice(ctx, "Usage: !persona <persona> <message>", reason="invalid_persona_usage")
      return
    parts = request.strip().split(None, 1)
    if len(parts) < 2:
      await self._queue_channel_notice(ctx, "Usage: !persona <persona> <message>", reason="invalid_persona_usage")
      return

    persona = parts[0].strip()
    message = parts[1].strip()
    metadata = {
      "guild_id": guild_id,
      "channel_id": channel_id,
      "user_id": user_id,
    }

    try:
      resp = await dispatch_rpc_op(
        self.discord.app,
        "urn:discord:chat:persona_command:1",
        {
          "persona": persona,
          "message": message,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
        },
        discord_ctx=metadata,
      )
      payload = resp.payload
      if hasattr(payload, "model_dump"):
        data = payload.model_dump()
      elif isinstance(payload, dict):
        data = dict(payload)
      else:
        data = {"success": bool(payload)}

      if not data.get("success"):
        ack = data.get("ack_message") or "Persona chat is currently unavailable."
        await self._queue_channel_notice(ctx, ack, reason=data.get("reason") or "persona_failed")
    except Exception:
      elapsed = time.perf_counter() - start
      logging.exception(
        "[DiscordInputProvider] persona failed",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "request": request,
          "elapsed": elapsed,
        },
      )
      await self._queue_channel_notice(ctx, "Persona chat is currently unavailable.", reason="persona_rpc_failure")
      return

    elapsed = time.perf_counter() - start
    logging.info(
      "[DiscordInputProvider] persona",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "persona": persona,
        "success": data.get("success"),
        "reason": data.get("reason"),
        "elapsed": elapsed,
      },
    )

  async def _queue_channel_notice(self, ctx, message: str, *, reason: str | None = None) -> None:
    channel_id = getattr(ctx.channel, "id", 0)
    guild_id = getattr(ctx.guild, "id", 0)
    user_id = getattr(ctx.author, "id", 0)
    module = getattr(self.discord.app.state, "discord_chat", None)
    if module:
      try:
        await module.deliver_summary(
          guild_id=guild_id,
          channel_id=channel_id,
          user_id=user_id,
          summary_text=None,
          ack_message=message,
          success=False,
          reason=reason,
        )
        return
      except Exception:
        logging.exception(
          "[DiscordInputProvider] failed to queue channel notice",
          extra={
            "channel_id": channel_id,
            "guild_id": guild_id,
            "user_id": user_id,
            "reason": reason,
          },
        )
    try:
      await self.discord.queue_channel_message(channel_id, message)
      return
    except Exception:
      logging.exception(
        "[DiscordInputProvider] failed to queue channel message",
        extra={"channel_id": channel_id},
      )
    try:
      await self.discord.send_channel_message(channel_id, message)
    except Exception:
      logging.exception(
        "[DiscordInputProvider] failed to send channel message",
        extra={"channel_id": channel_id},
      )
