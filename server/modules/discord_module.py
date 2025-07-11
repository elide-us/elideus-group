from fastapi import FastAPI
from . import BaseModule
from server.helpers.logging import configure_discord_logging, remove_discord_logging
import logging

"""Discord provider using environment variables from EnvironmentProvider."""

import discord, asyncio
from discord.ext import commands

class DiscordModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.env = app.state.modules.get_module("env")
    self.secret: str | None = None
    self.syschan: int | None = None
    self.bot = self._init_discord_bot('!')
    self.bot.app = self.app

  def _init_discord_bot(self, prefix: str) -> commands.Bot:
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.members = True
    intents.message_content = True
    return commands.Bot(command_prefix=prefix, intents=intents)

  def _init_bot_routes(self):
    bot = self.bot
    syschan = self.syschan

    @bot.event
    async def on_ready():
      channel = bot.get_channel(syschan)
      if channel:
        await channel.send("TheOracleRPC Online.")
        logging.info("Discord bot ready")
      else:
        print("[DiscordProvider] System channel not found on ready.")

    @bot.event
    async def on_guild_join(guild):
      channel = bot.get_channel(syschan)
      if channel:
        await channel.send(f"Joined {guild.name} ({guild.id})")
        logging.info(f"Joined guild {guild.name} ({guild.id})")
      else:
        print(f"[DiscordProvider] System channel not found when joining {guild.name}.")

  async def _start_discord_bot(self):
    await self.bot.start(self.secret)

  async def startup(self):
    self.secret = self.env.get("DISCORD_SECRET")
    self.syschan = self.env.get_int("DISCORD_SYSCHAN")
    self._init_bot_routes()
    configure_discord_logging(self)
    logging.info("Discord module loaded")
    self.task = asyncio.create_task(self._start_discord_bot())

  async def shutdown(self):
    await self.bot.close()
    if self.task:
      self.task.cancel()
    remove_discord_logging(self)

  async def send_sys_message(self, message: str):
    channel = self.bot.get_channel(self.syschan)
    if channel:
      await channel.send(message)
