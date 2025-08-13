import logging, discord, asyncio, json
from fastapi import FastAPI, Request
from discord.ext import commands

from . import BaseModule
from .env_module import EnvModule
from .db_module import DbModule

from server.helpers.logging import configure_discord_logging, remove_discord_logging

class DiscordModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.secret: str = ""
    self.syschan: int = 0
    self.task: asyncio.Task | None = None
    self.bot: commands.Bot | None = None
    self.db: DbModule | None = None
    self.env: EnvModule | None = None
    
  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.secret = self.env.get("DISCORD_SECRET")
    self.bot = self._init_discord_bot('!')
    self.bot.app = self.app
    self._init_bot_routes()
    configure_discord_logging(self)
    res = await self.db.run("db:system:config:get_config:1", {"key": "DiscordSyschan"})
    if not res.rows:
      raise ValueError("Missing config value for key: DiscordSyschan")
    self.syschan = int(res.rows[0]["value"] or 0)
    self.task = asyncio.create_task(self.bot.start(self.secret))
    logging.info("Discord module loaded")
    self.mark_ready()

  async def shutdown(self):
    if self.bot:
      await self.bot.close()
    if self.task:
      self.task.cancel()
    remove_discord_logging(self)

  def _init_discord_bot(self, prefix: str) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guild_messages = True
    intents.guilds = True
    intents.members = True
    intents.message_content = True
    return commands.Bot(command_prefix=prefix, intents=intents)

  async def send_sys_message(self, message: str):
    if not self.bot or not self.syschan:
      return
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
        res = await self.db.run("db:system:config:get_config:1", {"key": "Version"})
        version = res.rows[0]["value"] if res.rows else None
        logging.info(f"TheOracleGPT-Dev Online. Version: {version or 'unknown'}")
      else:
        logging.warning("[DiscordProvider] System channel not found on ready.")

    @self.bot.event
    async def on_guild_join(guild):
      channel = self.bot.get_channel(self.syschan)
      if channel:
        logging.info(f"Joined guild {guild.name} ({guild.id})")
      else:
        logging.warning(f"[DiscordProvider] System channel not found when joining {guild.name}.")

    @self.bot.command(name="rpc")
    async def rpc_command(ctx, *, op: str):
      req = Request({"type": "http", "app": self.app, "headers": []})
      from rpc.handler import handle_rpc_request
      from rpc.models import RPCRequest

      rpc_req = RPCRequest(op=op)
      try:
        resp = await handle_rpc_request(rpc_req, req)
        payload = resp.payload

        if hasattr(payload, "model_dump"):
          data = json.dumps(payload.model_dump())
        else:
          data = str(payload)
        await ctx.send(data)
      except Exception as e:
        await ctx.send(f"Error: {e}")

