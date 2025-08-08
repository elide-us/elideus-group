import logging, discord, asyncio, json
from .env_module import EnvironmentModule
from server.modules.database_provider import DatabaseProvider
from fastapi import FastAPI, Request
from discord.ext import commands
from server.helpers.logging import configure_discord_logging #, remove_discord_logging

class DiscordModule():
  def __init__(self, app: FastAPI):
    self.app: FastAPI = app
    try:
      self.env: EnvironmentModule = app.state.env
      self.db: DatabaseProvider = app.state.mssql
    except AttributeError:
      raise Exception("Env and Database modules must be loaded first")
    self.secret = self.env.get("DISCORD_SECRET")
    self.bot = self._init_discord_bot('!')
    self.bot.app = self.app
    self.syschan = 0
    self.task = None
    self._init_bot_routes()
    configure_discord_logging(self)

    logging.info("Discord module loaded")

  async def startup(self):
    val = await self.db.get_config_value("DiscordSyschan")
    self.syschan = int(val or 0)
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
      from server.helpers.logging import split_message
      for part in split_message(message):
        await channel.send(part)

  # This will be moved to discord_router at a later time
  def _init_bot_routes(self):
    @self.bot.event
    async def on_ready():
      channel = self.bot.get_channel(self.syschan)
      if channel:
        version = await self.db.get_config_value("Version")
        if version:
          await channel.send(f"TheOracleRPC Online. Version: {version}")
        else:
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

    @self.bot.command(name="rpc")
    async def rpc_command(ctx, *, op: str):
      req = Request({"type": "http", "app": self.app, "headers": []})
      from rpc.handler import handle_rpc_request
      from rpc.models import RPCRequest

      parts = op.split(":")
      if "view" not in parts:
        op = f"{op}:view:discord:1"

      rpc_req = RPCRequest(op=op)
      try:
        resp = await handle_rpc_request(rpc_req, req)
        payload = resp.payload

        if hasattr(payload, "content"):
          await ctx.send(payload.content)
          return

        if hasattr(payload, "model_dump"):
          data = json.dumps(payload.model_dump())
        else:
          data = str(payload)
        await ctx.send(data)
      except Exception as e:
        await ctx.send(f"Error: {e}")

  # async def shutdown(self):
  #   await self.bot.close()
  #   if self.task:
  #     self.task.cancel()
  #   remove_discord_logging(self)

