from fastapi import FastAPI
from . import Provider

from server.config import get_discord_secret, get_discord_syschan

import discord, asyncio
from discord.ext import commands

class DiscordProvider(Provider):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.secret = get_discord_secret()
    self.syschan = get_discord_syschan()
    self.bot = self._init_discord_bot('!')
    self.bot.app = self.app
    self._init_bot_routes()

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
      else:
        print("[DiscordProvider] System channel not found on ready.")

    @bot.event
    async def on_guild_join(guild):
      channel = bot.get_channel(syschan)
      if channel:
        await channel.send(f"Joined {guild.name} ({guild.id})")
      else:
        print(f"[DiscordProvider] System channel not found when joining {guild.name}.")

  async def _start_discord_bot(self):
    await self.bot.start(self.secret)

  async def startup(self):
    self.task = asyncio.create_task(self._start_discord_bot())

  async def shutdown(self):
    await self.bot.close()
    if self.task:
      self.task.cancel()
