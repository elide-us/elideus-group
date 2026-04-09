"""Discord bot coordination module."""

import asyncio, logging, os, time, discord
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import IO, TYPE_CHECKING, Any, NamedTuple

from discord.ext import commands
from fastapi import FastAPI

try:  # pragma: no cover - platform dependent import
  import fcntl
except ImportError:  # pragma: no cover - Windows fallback handled later
  fcntl = None

try:  # pragma: no cover - platform dependent import
  import msvcrt
except ImportError:  # pragma: no cover - non-Windows platforms
  msvcrt = None

from queryregistry.discord.guilds import (
  get_guild_request,
  list_guilds_request,
  update_credits_request,
  upsert_guild_request,
)
from queryregistry.discord.guilds.models import (
  GuildIdParams,
  ListGuildsParams,
  UpdateGuildCreditsParams,
  UpsertGuildParams,
)
from queryregistry.system.config import get_config_request
from queryregistry.system.config.models import ConfigKeyParams
from server.helpers.logging import configure_discord_logging, remove_discord_logging, update_logging_level
from server.routers.discord_events import register_discord_event_handlers

from . import BaseModule
from .db_module import DbModule
from .env_module import EnvModule

if TYPE_CHECKING:  # pragma: no cover
  DiscordAuthModule = Any

_SendCallable = Callable[[str], Awaitable[None]]


class _QueuePayload(NamedTuple):
  kind: str
  target_id: int
  message: str


class DiscordBotModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.secret: str = ""
    self.syschan: int = 0
    self.bot: commands.Bot | None = None
    self.db: DbModule | None = None
    self.env: EnvModule | None = None
    self.discord_auth: "DiscordAuthModule" | None = None
    self._task: asyncio.Task | None = None
    self._worker_task: asyncio.Task[None] | None = None
    self._message_size_limit = 1998
    self._trickle_delay = 1.0
    self._send_lock = asyncio.Lock()
    self._outbound_queue: asyncio.Queue[_QueuePayload] = asyncio.Queue()
    self._stats_lock = asyncio.Lock()
    self._channel_stats: dict[int, dict[str, float | int]] = {}
    self._user_stats: dict[int, dict[str, float | int]] = {}
    self._aggregate_stats: dict[str, float | int] = {"messages": 0, "characters": 0, "last_sent_at": 0.0}
    self.owns_bot: bool = False
    self._lock_handle: IO[str] | None = None
    self.auth_module: "DiscordAuthModule" | None = None
    if not getattr(self.app.state, "discord_bot", None):
      setattr(self.app.state, "discord_bot", self)

  async def startup(self):
    self.env = self.app.state.env
    await self.env.on_ready()
    self.db = self.app.state.db
    await self.db.on_ready()
    self.discord_auth = getattr(self.app.state, "discord_auth", None) or getattr(self.app.state, "auth", None)
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
      try:
        await self.bot.login(self.secret)
        self._task = asyncio.create_task(self.bot.connect())
        await self.bot.wait_until_ready()
      except Exception:
        logging.exception("Failed to start Discord bot")
        if self._task:
          self._task.cancel()
        raise

      register_discord_event_handlers(self)
      update_logging_level(self.db.logging_level)
      configure_discord_logging(self)
      res = await self.db.run(get_config_request(ConfigKeyParams(key="DiscordSyschan")))
      if not res.rows:
        raise ValueError("Missing config value for key: DiscordSyschan")
      self.syschan = int(res.rows[0]["element_value"] or 0)
      if not self._worker_task:
        self._worker_task = asyncio.create_task(self._queue_worker(), name="discord-output-worker")
      setattr(self.app.state, "discord_bot", self)
      setattr(self.app.state, "discord_output", self)
    except Exception:
      if self._worker_task:
        self._worker_task.cancel()
        with suppress(asyncio.CancelledError):
          await self._worker_task
      self._worker_task = None
      if self._task and not self._task.cancelled():
        self._task.cancel()
      self._task = None
      remove_discord_logging(self)
      self.bot = None
      self._release_bot_lock()
      self.owns_bot = False
      if getattr(self.app.state, "discord_bot", None) is self:
        self.app.state.discord_bot = None
      if getattr(self.app.state, "discord_output", None) is self:
        self.app.state.discord_output = None
      raise

    logging.debug("Discord bot module loaded")
    self.mark_ready()

  async def shutdown(self):
    if self._worker_task:
      self._worker_task.cancel()
      with suppress(asyncio.CancelledError):
        await self._worker_task
      self._worker_task = None

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
    if getattr(self.app.state, "discord_output", None) is self:
      self.app.state.discord_output = None

  def _init_discord_bot(self, prefix: str) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guild_messages = True
    intents.guilds = True
    intents.members = True
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

  def configure_message_window(self, max_message_size: int) -> None:
    if max_message_size <= 0:
      raise ValueError("max_message_size must be greater than zero")
    self._message_size_limit = max_message_size

  def configure_trickle_rate(self, delay_seconds: float) -> None:
    if delay_seconds < 0:
      raise ValueError("delay_seconds cannot be negative")
    self._trickle_delay = delay_seconds

  async def send_channel_message(self, channel_id: int, message: str) -> None:
    await self.send_to_channel(channel_id, message)

  async def send_user_message(self, user_id: int, message: str) -> None:
    await self.send_to_user(user_id, message)

  async def send_to_channel(self, channel_id: int, message: str) -> None:
    if not message:
      return
    channel = await self._resolve_channel(channel_id)
    await self._deliver_in_chunks(channel.send, message)
    await self._record_channel_throughput(channel_id, message)

  async def send_to_user(self, user_id: int, message: str) -> None:
    if not message:
      return
    user = await self._resolve_user(user_id)
    await self._deliver_in_chunks(user.send, message)
    await self._record_user_throughput(user_id, message)

  async def queue_channel_message(self, channel_id: int, message: str) -> None:
    if not message:
      return
    await self._outbound_queue.put(_QueuePayload("channel", channel_id, message))

  async def queue_user_message(self, user_id: int, message: str) -> None:
    if not message:
      return
    await self._outbound_queue.put(_QueuePayload("user", user_id, message))

  async def wait_for_drain(self) -> None:
    await self._outbound_queue.join()

  async def get_throughput_snapshot(self) -> dict[str, dict]:
    async with self._stats_lock:
      return {
        "aggregate": dict(self._aggregate_stats),
        "channels": {cid: dict(stats) for cid, stats in self._channel_stats.items()},
        "users": {uid: dict(stats) for uid, stats in self._user_stats.items()},
      }

  async def _resolve_channel(self, channel_id: int) -> discord.abc.Messageable:
    if not self.bot:
      raise RuntimeError("Discord bot is not available")
    channel = self.bot.get_channel(channel_id)
    if channel is None:
      try:
        channel = await self.bot.fetch_channel(channel_id)
      except discord.DiscordException:
        logging.exception("[DiscordBotModule] failed to fetch channel", extra={"channel_id": channel_id})
        raise
    if not hasattr(channel, "send"):
      raise RuntimeError(f"Channel {channel_id} is not send-capable")
    return channel

  async def _resolve_user(self, user_id: int) -> discord.abc.Messageable:
    if not self.bot:
      raise RuntimeError("Discord bot is not available")
    user = self.bot.get_user(user_id)
    if user is None:
      try:
        user = await self.bot.fetch_user(user_id)
      except discord.DiscordException:
        logging.exception("[DiscordBotModule] failed to fetch user", extra={"user_id": user_id})
        raise
    if not hasattr(user, "send"):
      raise RuntimeError(f"User {user_id} cannot receive messages")
    return user

  async def _queue_worker(self) -> None:
    while True:
      try:
        payload = await self._outbound_queue.get()
      except asyncio.CancelledError:
        raise
      try:
        if payload.kind == "channel":
          await self.send_to_channel(payload.target_id, payload.message)
        else:
          await self.send_to_user(payload.target_id, payload.message)
      except asyncio.CancelledError:
        raise
      except Exception:  # pragma: no cover - observability path
        logging.exception(
          "[DiscordBotModule] failed to dispatch message",
          extra={"kind": payload.kind, "target": payload.target_id},
        )
      finally:
        self._outbound_queue.task_done()

  async def _deliver_in_chunks(self, sender: _SendCallable, text: str) -> None:
    chunks = self._yield_chunks(text, self._message_size_limit)
    async with self._send_lock:
      for chunk in chunks:
        await sender(chunk)
        if self._trickle_delay > 0:
          await asyncio.sleep(self._trickle_delay)

  async def _record_channel_throughput(self, channel_id: int, message: str) -> None:
    await self._record_stats(self._channel_stats, channel_id, message)

  async def _record_user_throughput(self, user_id: int, message: str) -> None:
    await self._record_stats(self._user_stats, user_id, message)

  async def _record_stats(self, bucket: dict[int, dict[str, float | int]], identifier: int, message: str) -> None:
    async with self._stats_lock:
      stats = bucket.setdefault(identifier, {"messages": 0, "characters": 0, "last_sent_at": 0.0})
      now = time.time()
      stats["messages"] += 1
      stats["characters"] += len(message)
      stats["last_sent_at"] = now
      self._aggregate_stats["messages"] += 1
      self._aggregate_stats["characters"] += len(message)
      self._aggregate_stats["last_sent_at"] = now

  @staticmethod
  def _wrap_line(line: str, max_message_size: int) -> list[str]:
    remaining = line
    parts: list[str] = []
    while remaining:
      if len(remaining) <= max_message_size:
        parts.append(remaining)
        break
      window = remaining[:max_message_size]
      split = window.rfind(" ")
      if split <= 0:
        split = max_message_size
      parts.append(remaining[:split])
      remaining = remaining[split:]
    if not parts:
      parts.append("")
    return parts

  @classmethod
  def _yield_chunks(cls, text: str, max_message_size: int) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    chunks: list[str] = []
    buffer = ""
    for raw_line in lines:
      line = raw_line
      if not line.strip() and not buffer.strip():
        continue
      wrapped = cls._wrap_line(line, max_message_size)
      for segment in wrapped[:-1]:
        candidate = segment if not buffer else buffer + "\n" + segment
        if candidate.strip() and candidate.strip() != "---":
          chunks.append(candidate)
        buffer = ""
      last_segment = wrapped[-1]
      candidate = last_segment if not buffer else buffer + ("\n" + last_segment if last_segment else "\n")
      if len(candidate) <= max_message_size:
        buffer = candidate
      else:
        if buffer.strip() and buffer.strip() != "---":
          chunks.append(buffer)
        buffer = last_segment
    if buffer.strip() and buffer.strip() != "---":
      chunks.append(buffer)
    return chunks

  async def _try_send_channel(self, channel_id: int, message: str) -> bool:
    try:
      await self.send_to_channel(channel_id, message)
      return True
    except Exception:
      logging.exception(
        "[DiscordBotModule] failed to send channel message",
        extra={"channel_id": channel_id},
      )
      return False

  async def _try_send_user(self, user_id: int, message: str) -> bool:
    try:
      await self.send_to_user(user_id, message)
      return True
    except Exception:
      logging.exception(
        "[DiscordBotModule] failed to send user message",
        extra={"user_id": user_id},
      )
      return False

  async def send_sys_message(self, message: str):
    if not self.syschan:
      return
    try:
      await self.send_to_channel(self.syschan, message)
    except Exception:
      logging.exception("[DiscordBotModule] failed to send sys message")

  def _map_guild_row(self, row: dict[str, Any], guild_id: str = "") -> dict[str, Any]:
    return {
      "recid": row.get("recid", 0),
      "guild_id": row.get("element_guild_id", guild_id),
      "name": row.get("element_name", ""),
      "joined_on": row.get("element_joined_on"),
      "member_count": row.get("element_member_count"),
      "owner_id": row.get("element_owner_id"),
      "region": row.get("element_region"),
      "left_on": row.get("element_left_on"),
      "notes": row.get("element_notes"),
      "credits": int(row.get("element_credits", 0) or 0),
    }

  async def list_guild_records(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_guilds_request(ListGuildsParams(include_inactive=True)))
    return [self._map_guild_row(row) for row in (res.rows or [])]

  async def get_guild_record(self, guild_id: str) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(get_guild_request(GuildIdParams(guild_id=guild_id)))
    row = res.rows[0] if res.rows else {}
    return self._map_guild_row(row, guild_id=guild_id)

  async def get_guild_credits(self, guild_id: str) -> int:
    guild = await self.get_guild_record(guild_id)
    return int(guild.get("credits", 0) or 0)

  async def update_guild_credits(self, guild_id: str, credits: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(
      update_credits_request(UpdateGuildCreditsParams(guild_id=guild_id, credits=credits))
    )
    return {"guild_id": guild_id, "credits": credits}

  async def sync_guild_records(self) -> dict[str, Any]:
    if not self.bot:
      logging.warning("[DiscordBotModule] Discord bot not available")
      return {"synced": 0, "guilds": []}
    assert self.db
    synced = 0
    for guild in self.bot.guilds:
      try:
        await self.db.run(
          upsert_guild_request(
            UpsertGuildParams(
              guild_id=str(guild.id),
              name=guild.name,
              member_count=guild.member_count,
              owner_id=str(guild.owner_id) if guild.owner_id else None,
            )
          )
        )
        synced += 1
      except Exception:
        logging.exception(
          "[DiscordBotModule] failed to upsert guild",
          extra={"guild_id": guild.id, "guild_name": guild.name},
        )
    guilds = await self.list_guild_records()
    logging.info("[DiscordBotModule] synced %d guilds", synced)
    return {"synced": synced, "guilds": guilds}


class DiscordModule(DiscordBotModule):
  """Backward-compatible alias for the DiscordBotModule."""
