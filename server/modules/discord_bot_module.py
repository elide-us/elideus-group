"""Discord bot coordination module."""

import logging, discord, json, asyncio, time, os
from typing import IO, TYPE_CHECKING, Any
from fastapi import FastAPI, Request
from discord.ext import commands

try:  # pragma: no cover - platform dependent import
  import fcntl
except ImportError:  # pragma: no cover - Windows fallback handled later
  fcntl = None

try:  # pragma: no cover - platform dependent import
  import msvcrt
except ImportError:  # pragma: no cover - non-Windows platforms
  msvcrt = None

from . import BaseModule
from .env_module import EnvModule
from .db_module import DbModule

from server.helpers.logging import configure_discord_logging, remove_discord_logging, update_logging_level

if TYPE_CHECKING:  # pragma: no cover
  from .discord_output_module import DiscordOutputModule
  from .auth_module import AuthModule

class DiscordBotModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.secret: str = ""
    self.syschan: int = 0
    self.bot: commands.Bot | None = None
    self.db: DbModule | None = None
    self.env: EnvModule | None = None
    self.discord_output: "DiscordOutputModule" | None = None
    self.discord_auth: "AuthModule" | None = None
    self.social_input_module: Any = None
    self.discord_input_provider: Any = None
    self._task: asyncio.Task | None = None
    self._user_counts: dict[int, int] = {}
    self._guild_counts: dict[int, int] = {}
    self.USER_RATE_LIMIT = 100
    self.GUILD_RATE_LIMIT = 1000
    self.owns_bot: bool = False
    self._lock_handle: IO[str] | None = None

  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.discord_output = getattr(self.app.state, "discord_output", None)
    self.discord_auth = getattr(self.app.state, "discord_auth", None) or getattr(self.app.state, "auth", None)
    self.social_input_module = getattr(self.app.state, "social_input", None)
    self.discord_input_provider = getattr(self.app.state, "discord_input_provider", None)
    setattr(self.app.state, "discord", self)
    if not self._acquire_bot_lock():
      logging.info("[DiscordBotModule] startup skipped: Discord bot already owned by another worker")
      self.mark_ready()
      return
    try:
      self.owns_bot = True
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
    except Exception:
      if self._task and not self._task.cancelled():
        self._task.cancel()
      self._task = None
      remove_discord_logging(self)
      self.bot = None
      self._release_bot_lock()
      self.owns_bot = False
      raise
    logging.info("[DiscordBotModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    if self.bot:
      await self.bot.close()
      self.bot = None
    if self._task:
      try:
        await self._task
      except asyncio.CancelledError:
        pass
      self._task = None
    remove_discord_logging(self)
    self._release_bot_lock()
    self.owns_bot = False
    logging.info("[DiscordBotModule] shutdown")

  def _init_discord_bot(self, prefix: str) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guild_messages = True
    intents.guilds = True
    intents.members = True
    intents.message_content = True
    return commands.Bot(command_prefix=prefix, intents=intents)

  def _acquire_bot_lock(self) -> bool:
    if self._lock_handle:
      return True
    lock_path = "/tmp/discord_bot.lock"
    try:
      os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    except OSError:
      pass
    handle = open(lock_path, "w")
    if not self._try_lock_file(handle):
      handle.close()
      return False
    self._lock_handle = handle
    return True

  def _try_lock_file(self, handle: IO[str]) -> bool:
    if fcntl:
      try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
      except BlockingIOError:
        return False
    if msvcrt:
      try:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        return True
      except OSError:
        return False
    return True

  def _release_bot_lock(self):
    if not self._lock_handle:
      return
    try:
      if fcntl:
        fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_UN)
      elif msvcrt:
        self._lock_handle.seek(0)
        msvcrt.locking(self._lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
      try:
        self._lock_handle.close()
      finally:
        self._lock_handle = None

  def _get_output_module(self) -> "DiscordOutputModule | None":
    if self.discord_output:
      return self.discord_output
    output = getattr(self.app.state, "discord_output", None)
    if output:
      self.discord_output = output
    return output

  async def _try_send_channel(self, channel_id: int, message: str) -> bool:
    output = self._get_output_module()
    if not output:
      return False
    try:
      await output.send_to_channel(channel_id, message)
      return True
    except Exception:
      logging.exception(
        "[DiscordBotModule] failed to send via DiscordOutputModule",
        extra={"channel_id": channel_id},
      )
    return False

  async def _try_send_user(self, user_id: int, message: str) -> bool:
    output = self._get_output_module()
    if not output:
      return False
    try:
      await output.send_to_user(user_id, message)
      return True
    except Exception:
      logging.exception(
        "[DiscordBotModule] failed to send user message via DiscordOutputModule",
        extra={"user_id": user_id},
      )
    return False

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
    if not self.syschan:
      return
    if await self._try_send_channel(self.syschan, message):
      return
    if not self.bot:
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
        if await self._try_send_channel(channel.id, msg):
          logging.info(msg)
        else:
          try:
            await channel.send(msg)
            logging.info(msg)
          except Exception:
            logging.exception("[DiscordBotModule] failed to send ready message")
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
        if not await self._try_send_channel(ctx.channel.id, data):
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
        message = f"Error: {e}"
        if not await self._try_send_channel(ctx.channel.id, message):
          await ctx.send(message)

    @self.bot.command(name="summarize")
    async def summarize_command(ctx, hours: str):
      from rpc.handler import handle_rpc_request
      start = time.perf_counter()
      self._bump_rate_limits(ctx.guild.id, ctx.author.id)

      try:
        hrs = int(hours)
      except ValueError:
        if not await self._try_send_channel(ctx.channel.id, "Usage: !summarize <hours>"):
          await ctx.send("Usage: !summarize <hours>")
        return
      if hrs < 1 or hrs > 336:
        if not await self._try_send_channel(ctx.channel.id, "Hours must be between 1 and 336"):
          await ctx.send("Hours must be between 1 and 336")
        return

      body = json.dumps({
        "op": "urn:discord:chat:summarize_channel:1",
        "payload": {
          "guild_id": ctx.guild.id,
          "channel_id": ctx.channel.id,
          "hours": hrs,
          "user_id": ctx.author.id,
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
          if not await self._try_send_channel(ctx.channel.id, "No messages found in the specified time range"):
            await ctx.send("No messages found in the specified time range")
          return
        if data.get("cap_hit"):
          if not await self._try_send_channel(ctx.channel.id, "Channel too active to summarize; message cap hit"):
            await ctx.send("Channel too active to summarize; message cap hit")
          return
        summary_text = data.get("summary") or json.dumps(data)
        try:
          openai = getattr(self.app.state, "openai", None)
          output = self._get_output_module()
          if openai and getattr(openai, "summary_queue", None) and output:
            await openai.summary_queue.add(output.send_to_user, ctx.author.id, summary_text)
          elif output:
            await output.send_to_user(ctx.author.id, summary_text)
          else:
            await ctx.author.send(summary_text)
          if ctx.author.dm_channel:
            async for _ in ctx.author.dm_channel.history(limit=1):
              break
        except discord.errors.HTTPException:
          if not await self._try_send_channel(ctx.channel.id, "Failed to send summary. Please try again later."):
            await ctx.send("Failed to send summary. Please try again later.")
          logging.exception("[DiscordBot] summarize send failed")
          return
        except Exception:
          if not await self._try_send_channel(ctx.channel.id, "Failed to send summary. Please try again later."):
            await ctx.send("Failed to send summary. Please try again later.")
          logging.exception("[DiscordBot] summarize delivery failed")
          return
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
            "model": data.get("model"),
            "role": data.get("role"),
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
        if not await self._try_send_channel(ctx.channel.id, "Failed to fetch messages. Please try again later."):
          await ctx.send("Failed to fetch messages. Please try again later.")

