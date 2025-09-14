"""Discord integration module."""

import logging, discord, json, asyncio, time
from fastapi import FastAPI, Request
from discord.ext import commands

from . import BaseModule
from .env_module import EnvModule
from .db_module import DbModule

from server.helpers.logging import configure_discord_logging, remove_discord_logging, update_logging_level

class DiscordModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.secret: str = ""
    self.syschan: int = 0
    self.bot: commands.Bot | None = None
    self.db: DbModule | None = None
    self.env: EnvModule | None = None
    self._task: asyncio.Task | None = None
    self._user_counts: dict[int, int] = {}
    self._guild_counts: dict[int, int] = {}
    self.USER_RATE_LIMIT = 100
    self.GUILD_RATE_LIMIT = 1000
    
  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.secret = self.env.get("DISCORD_SECRET")
    self.bot = self._init_discord_bot('!')
    self.bot.app = self.app
    self._init_bot_routes()
    update_logging_level(self.db.logging_level)
    configure_discord_logging(self)
    res = await self.db.run("db:system:config:get_config:1", {"key": "DiscordSyschan"})
    if not res.rows:
      raise ValueError("Missing config value for key: DiscordSyschan")
    self.syschan = int(res.rows[0]["value"] or 0)
    try:
      await self.bot.login(self.secret)
      self._task = asyncio.create_task(self.bot.connect())
      await self.bot.wait_until_ready()
    except Exception:
      logging.exception("Failed to start Discord bot")
      if self._task:
        self._task.cancel()
      raise
    logging.info("Discord module loaded")
    self.mark_ready()

  async def shutdown(self):
    if self.bot:
      await self.bot.close()
    if self._task:
      try:
        await self._task
      except asyncio.CancelledError:
        pass
    remove_discord_logging(self)

  def _init_discord_bot(self, prefix: str) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guild_messages = True
    intents.guilds = True
    intents.members = True
    intents.message_content = True
    return commands.Bot(command_prefix=prefix, intents=intents)

  def _bump_rate_limits(self, guild_id: int, user_id: int):
    u = self._user_counts.get(user_id, 0) + 1
    g = self._guild_counts.get(guild_id, 0) + 1
    self._user_counts[user_id] = u
    self._guild_counts[guild_id] = g
    if u >= int(self.USER_RATE_LIMIT * 0.8):
      logging.info("[DiscordBot] user nearing rate limit", extra={"user_id": user_id, "count": u})
    if g >= int(self.GUILD_RATE_LIMIT * 0.8):
      logging.info("[DiscordBot] guild nearing rate limit", extra={"guild_id": guild_id, "count": g})

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
        msg = f"TheOracleGPT-Dev Online. Version: {version or 'unknown'}"
        await channel.send(msg)
        logging.info(msg)
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
      from rpc.handler import handle_rpc_request
      start = time.perf_counter()
      self._bump_rate_limits(ctx.guild.id, ctx.author.id)
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
        "app": self.app,
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
        await ctx.send(data)
        elapsed = time.perf_counter() - start
        logging.info(
          "[DiscordBot] rpc",
          extra={
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "user_id": ctx.author.id,
            "op": op,
            "elapsed": elapsed,
          },
        )
      except Exception as e:
        elapsed = time.perf_counter() - start
        logging.exception(
          "[DiscordBot] rpc failed",
          extra={"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "user_id": ctx.author.id, "op": op, "elapsed": elapsed},
        )
        await ctx.send(f"Error: {e}")

    @self.bot.command(name="summarize")
    async def summarize_command(ctx, hours: str):
      from rpc.handler import handle_rpc_request
      start = time.perf_counter()
      self._bump_rate_limits(ctx.guild.id, ctx.author.id)

      try:
        hrs = int(hours)
      except ValueError:
        await ctx.send("Usage: !summarize <hours>")
        return
      if hrs < 1 or hrs > 336:
        await ctx.send("Hours must be between 1 and 336")
        return

      body = json.dumps({
        "op": "urn:discord:chat:summarize_channel:1",
        "payload": {
          "guild_id": ctx.guild.id,
          "channel_id": ctx.channel.id,
          "hours": hrs,
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
        "app": self.app,
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
          await ctx.send("No messages found in the specified time range")
          return
        if data.get("cap_hit"):
          await ctx.send("Channel too active to summarize; message cap hit")
          return
        summary_text = data.get("summary") or json.dumps(data)
        await ctx.author.send(summary_text)
        if ctx.author.dm_channel:
          async for _ in ctx.author.dm_channel.history(limit=1):
            break
        elapsed = time.perf_counter() - start
        logging.info(
          "[DiscordBot] summarize",
          extra={
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "user_id": ctx.author.id,
            "hours": hrs,
            "token_count_estimate": data.get("token_count_estimate"),
            "messages_collected": data.get("messages_collected"),
            "cap_hit": data.get("cap_hit"),
            "elapsed": elapsed,
          },
        )
        logging.debug("[DiscordBot] summarize response", extra=data)
      except Exception:
        elapsed = time.perf_counter() - start
        logging.exception(
          "[DiscordBot] summarize failed",
          extra={"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "user_id": ctx.author.id, "hours": hrs, "elapsed": elapsed},
        )
        await ctx.send("Failed to fetch messages. Please try again later.")

    @self.bot.command(name="uwu")
    async def uwu_command(ctx, *, text: str):
      from rpc.handler import handle_rpc_request
      start = time.perf_counter()
      self._bump_rate_limits(ctx.guild.id, ctx.author.id)

      body = json.dumps({
        "op": "urn:discord:chat:uwu_chat:1",
        "payload": {
          "guild_id": ctx.guild.id,
          "channel_id": ctx.channel.id,
          "user_id": ctx.author.id,
          "message": text,
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
        "app": self.app,
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
          data = {"message": str(payload)}
        response_text = data.get("uwu_response_text") or data.get("message") or json.dumps(data)
        await ctx.send(response_text)
        async for _ in ctx.channel.history(limit=1):
          break
        elapsed = time.perf_counter() - start
        logging.info(
          "[DiscordBot] uwu",
          extra={
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "user_id": ctx.author.id,
            "token_count_estimate": data.get("token_count_estimate"),
            "elapsed": elapsed,
          },
        )
        logging.debug("[DiscordBot] uwu response", extra=data)
      except Exception as e:
        elapsed = time.perf_counter() - start
        logging.exception(
          "[DiscordBot] uwu failed",
          extra={"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "user_id": ctx.author.id, "elapsed": elapsed},
        )
        await ctx.send(f"Error: {e}")

