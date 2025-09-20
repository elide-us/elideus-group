import asyncio, logging
from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from server.modules.discord_bot_module import DiscordBotModule
from server.routers.discord_events import register_discord_event_handlers


class DummyChannel:
  def __init__(self, channel_id: int = 123):
    self.id = channel_id
    self.messages: list[str] = []

  async def send(self, message: str):
    self.messages.append(message)


class DummyBot:
  def __init__(self, channels: dict[int, DummyChannel] | None = None):
    self.channels = channels or {}
    self.events: dict[str, object] = {}

  def event(self, fn):
    self.events[fn.__name__] = fn
    return fn

  def get_channel(self, channel_id: int):
    return self.channels.get(channel_id)


class DummyDb:
  def __init__(self, values: dict[str, str | None]):
    self.values = values
    self.calls: list[tuple[str, dict]] = []

  async def run(self, op: str, args: dict):
    self.calls.append((op, args))
    value = self.values.get(args.get("key"))
    rows = [{"value": value}] if value is not None else []
    return SimpleNamespace(rows=rows, rowcount=len(rows))


def _build_module(db_values: dict[str, str | None], channel: DummyChannel | None = None) -> tuple[DiscordBotModule, DummyBot]:
  app = FastAPI()
  module = DiscordBotModule(app)
  module.db = DummyDb(db_values)
  module.syschan = 123
  bot = DummyBot({channel.id: channel} if channel else {})
  module.bot = bot
  return module, bot


def test_on_ready_uses_output_module(caplog):
  channel = DummyChannel()
  module, bot = _build_module({"Version": "1.2.3", "BotName": "TestBot"}, channel)

  captured: dict[str, str] = {}

  async def fake_try_send(channel_id: int, message: str) -> bool:
    captured["channel_id"] = channel_id
    captured["message"] = message
    return True

  module._try_send_channel = fake_try_send

  register_discord_event_handlers(module)

  with caplog.at_level(logging.INFO):
    asyncio.run(bot.events["on_ready"]())

  assert captured == {"channel_id": 123, "message": "TestBot Online. Version: 1.2.3"}
  assert any(record.message == "TestBot Online. Version: 1.2.3" for record in caplog.records)


def test_on_ready_channel_fallback(caplog):
  channel = DummyChannel()
  module, bot = _build_module({}, channel)

  async def fake_try_send(channel_id: int, message: str) -> bool:
    return False

  module._try_send_channel = fake_try_send

  register_discord_event_handlers(module)

  with caplog.at_level(logging.INFO):
    asyncio.run(bot.events["on_ready"]())

  assert channel.messages == ["TheOracleGPT-Dev Online. Version: unknown"]
  assert any(record.message == "TheOracleGPT-Dev Online. Version: unknown" for record in caplog.records)


def test_on_ready_missing_channel_logs_warning(caplog):
  module, bot = _build_module({})

  register_discord_event_handlers(module)

  with caplog.at_level(logging.WARNING):
    asyncio.run(bot.events["on_ready"]())

  assert any("System channel not found on ready" in record.message for record in caplog.records)


def test_on_guild_join_logs(caplog):
  channel = DummyChannel()
  module, bot = _build_module({}, channel)

  register_discord_event_handlers(module)

  guild = SimpleNamespace(name="Guild", id=456)

  with caplog.at_level(logging.INFO):
    asyncio.run(bot.events["on_guild_join"](guild))

  assert any("Joined guild Guild (456)" in record.message for record in caplog.records)

  module.syschan = 999

  with caplog.at_level(logging.WARNING):
    asyncio.run(bot.events["on_guild_join"](guild))

  assert any("System channel not found when joining" in record.message for record in caplog.records)


def test_register_requires_bot():
  app = FastAPI()
  module = DiscordBotModule(app)
  module.bot = None

  with pytest.raises(RuntimeError):
    register_discord_event_handlers(module)
