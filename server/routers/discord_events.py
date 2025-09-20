"""Discord bot event handlers."""

import logging
from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:  # pragma: no cover - runtime import cycle guard
  from server.modules.discord_bot_module import DiscordBotModule


def register_discord_event_handlers(bot_module: "DiscordBotModule") -> None:
  """Register Discord bot lifecycle events for the provided module."""
  bot = bot_module.bot
  if not bot:
    raise RuntimeError("Discord bot has not been initialized")

  _register_on_ready_handler(bot_module, bot)
  _register_on_guild_join_handler(bot_module, bot)


def _register_on_ready_handler(bot_module: "DiscordBotModule", bot: commands.Bot) -> None:
  @bot.event
  async def on_ready():
    channel = bot.get_channel(bot_module.syschan)
    if channel:
      res = await bot_module.db.run("db:system:config:get_config:1", {"key": "Version"})
      version = res.rows[0]["value"] if res.rows else None
      name_res = await bot_module.db.run("db:system:config:get_config:1", {"key": "BotName"})
      bot_name = name_res.rows[0]["value"] if name_res.rows else None
      msg = f"{(bot_name or 'TheOracleGPT-Dev')} Online. Version: {version or 'unknown'}"
      if await bot_module._try_send_channel(channel.id, msg):
        logging.info(msg)
      else:
        try:
          await channel.send(msg)
          logging.info(msg)
        except Exception:
          logging.exception("[DiscordBotModule] failed to send ready message")
    else:
      logging.warning("[DiscordProvider] System channel not found on ready.")


def _register_on_guild_join_handler(bot_module: "DiscordBotModule", bot: commands.Bot) -> None:
  @bot.event
  async def on_guild_join(guild):
    channel = bot.get_channel(bot_module.syschan)
    if channel:
      logging.info(f"Joined guild {guild.name} ({guild.id})")
    else:
      logging.warning(f"[DiscordProvider] System channel not found when joining {guild.name}.")
