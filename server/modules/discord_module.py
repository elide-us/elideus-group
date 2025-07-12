import logging, discord, asyncio
from .env_module import EnvironmentModule
from fastapi import FastAPI
from discord.ext import commands
from server.helpers.logging import configure_discord_logging #, remove_discord_logging

class DiscordModule():
  def __init__(self, app: FastAPI):
    self.app: FastAPI = app
    try:
      self.env: EnvironmentModule = app.state.env
    except AttributeError:
      raise Exception("Env module must be initialized first")
    self.secret = self.env.get("DISCORD_SECRET")
    self.bot = self._init_discord_bot('!')
    self.bot.app = self.app

    self.syschan = self.env.get_as_int("DISCORD_SYSCHAN")
    self._init_bot_routes(self)
    configure_discord_logging(self)

    logging.info("Discord module loaded")

    self.task = asyncio.create_task(self.bot.start(self.secret))

  def _init_discord_bot(self, prefix: str) -> commands.Bot:
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.members = True
    intents.message_content = True
    return commands.Bot(command_prefix=prefix, intents=intents)

  async def send_sys_message(self, message: str):
    channel = self.bot.get_channel(self.syschan)
    if channel:
      await channel.send(message)

  # This will be moved to discord_router at a later time
  def _init_bot_routes(self):
    @self.bot.event
    async def on_ready():
      channel = self.bot.get_channel(self.syschan)
      if channel:
        await channel.send("TheOracleRPC Online.")
        logging.info("Discord bot ready")
      else:
        print("[DiscordProvider] System channel not found on ready.")

    @self.bot.event
    async def on_guild_join(guild):
      channel = self.bot.get_channel(self.syschan)
      if channel:
        await channel.send(f"Joined {guild.name} ({guild.id})")
        logging.info(f"Joined guild {guild.name} ({guild.id})")
      else:
        print(f"[DiscordProvider] System channel not found when joining {guild.name}.")

  # async def shutdown(self):
  #   await self.bot.close()
  #   if self.task:
  #     self.task.cancel()
  #   remove_discord_logging(self)

