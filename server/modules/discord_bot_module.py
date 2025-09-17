"""Discord bot coordination module."""

import logging, discord, asyncio, os
from typing import IO, TYPE_CHECKING, Any
from fastapi import FastAPI
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
  DiscordAuthModule = Any
  SocialInputModule = Any
  DiscordInputProvider = Any


class DiscordBotModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.secret: str = ""
    self.syschan: int = 0
    self.bot: commands.Bot | None = None
    self.db: DbModule | None = None
    self.env: EnvModule | None = None
    self.discord_output: "DiscordOutputModule" | None = None
    self.discord_auth: "DiscordAuthModule" | None = None
    self._task: asyncio.Task | None = None
    self._user_counts: dict[int, int] = {}
    self._guild_counts: dict[int, int] = {}
    self.USER_RATE_LIMIT = 100
    self.GUILD_RATE_LIMIT = 1000
    self.owns_bot: bool = False
    self._lock_handle: IO[str] | None = None
    self.auth_module: "DiscordAuthModule" | None = None
    self.output_module: "DiscordOutputModule" | None = None
    self.social_input_module: "SocialInputModule" | None = None
    self.input_provider: "DiscordInputProvider" | None = None
    if not getattr(self.app.state, "discord_bot", None):
      setattr(self.app.state, "discord_bot", self)

  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.discord_output = getattr(self.app.state, "discord_output", None)
    self.discord_auth = getattr(self.app.state, "discord_auth", None) or getattr(self.app.state, "auth", None)
    self.social_input_module = getattr(self.app.state, "social_input", None)
    setattr(self.app.state, "discord", self)
    if not self._acquire_bot_lock():
      logging.info("[DiscordBotModule] startup skipped: Discord bot already owned by another worker")
      self.mark_ready()
      return
    try:
      self.owns_bot = True
      setattr(self.app.state, "discord_bot", self)
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
      if getattr(self.app.state, "discord_bot", None) is self:
        self.app.state.discord_bot = None
      raise
    logging.info("Discord bot module loaded")
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
    if getattr(self.app.state, "discord_bot", None) is self:
      self.app.state.discord_bot = None

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

  def register_auth_module(self, module: "DiscordAuthModule") -> None:
    self.auth_module = module

  def register_output_module(self, module: "DiscordOutputModule") -> None:
    self.output_module = module

  def register_social_input_module(self, module: "SocialInputModule") -> None:
    self.social_input_module = module

  def register_input_provider(self, provider: "DiscordInputProvider") -> None:
    self.input_provider = provider

  def _get_output_module(self) -> "DiscordOutputModule | None":
    if self.output_module:
      return self.output_module
    output = getattr(self.app.state, "discord_output", None)
    if output:
      self.output_module = output
    return output

  def _require_output_module(self) -> "DiscordOutputModule":
    output = self._get_output_module()
    if not output:
      raise RuntimeError("DiscordOutputModule is not available")
    return output

  async def send_channel_message(self, channel_id: int, message: str) -> None:
    if not message:
      return
    output = self._require_output_module()
    await output.send_to_channel(channel_id, message)

  async def send_user_message(self, user_id: int, message: str) -> None:
    if not message:
      return
    output = self._require_output_module()
    await output.send_to_user(user_id, message)

  async def _try_send_channel(self, channel_id: int, message: str) -> bool:
    try:
      await self.send_channel_message(channel_id, message)
      return True
    except Exception:
      logging.exception(
        "[DiscordBotModule] failed to send via DiscordOutputModule",
        extra={"channel_id": channel_id},
      )
    return False

  async def _try_send_user(self, user_id: int, message: str) -> bool:
    try:
      await self.send_user_message(user_id, message)
      return True
    except Exception:
      logging.exception(
        "[DiscordBotModule] failed to send user message via DiscordOutputModule",
        extra={"user_id": user_id},
      )
    return False

  def bump_rate_limits(self, guild_id: int, user_id: int):
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

class DiscordModule(DiscordBotModule):
  """Backward-compatible alias for the DiscordBotModule."""

