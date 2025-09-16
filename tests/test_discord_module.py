import asyncio, logging
from fastapi import FastAPI

from server.modules import BaseModule
from server.modules.discord_module import DiscordModule


class DummyEnv(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self._env = {"DISCORD_SECRET": "secret"}

  async def startup(self):
    self.mark_ready()

  async def shutdown(self):
    pass

  def get(self, key: str):
    return self._env.get(key, "")


class DummyDb(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.logging_level = logging.INFO

  async def startup(self):
    self.mark_ready()

  async def shutdown(self):
    pass

  async def run(self, op: str, args: dict):
    class Res:
      def __init__(self, rows):
        self.rows = rows
        self.rowcount = len(rows)
    if op == "db:system:config:get_config:1" and args.get("key") == "DiscordSyschan":
      return Res([{ "value": "123" }])
    return Res([])


class DummyBot:
  def __init__(self):
    try:
      self.loop = asyncio.get_running_loop()
    except RuntimeError:
      self.loop = asyncio.get_event_loop()
    self.login_calls = 0
    self.connect_calls = 0
    self.wait_calls = 0

  def event(self, fn):
    return fn

  def command(self, name=None):
    def deco(fn):
      return fn
    return deco

  async def login(self, secret):
    self.login_calls += 1

  async def connect(self):
    self.connect_calls += 1

  async def wait_until_ready(self):
    self.wait_calls += 1

  def get_channel(self, channel_id):
    return None

  async def close(self):
    pass


def test_discord_module_startup_single_owner(monkeypatch, caplog):
  app = FastAPI()
  app.state.env = DummyEnv(app)
  app.state.db = DummyDb(app)
  asyncio.run(app.state.env.startup())
  asyncio.run(app.state.db.startup())

  created_bots: list[DummyBot] = []

  def fake_init(self, prefix: str):
    bot = DummyBot()
    created_bots.append(bot)
    return bot

  lock_attempts = {"count": 0}

  def fake_try_lock(self, handle):
    lock_attempts["count"] += 1
    return lock_attempts["count"] == 1

  monkeypatch.setattr(DiscordModule, "_init_discord_bot", fake_init)
  monkeypatch.setattr(DiscordModule, "_try_lock_file", fake_try_lock)

  module1 = DiscordModule(app)
  module2 = DiscordModule(app)

  with caplog.at_level(logging.INFO):
    asyncio.run(module1.startup())
    asyncio.run(module2.startup())

  assert module1.owns_bot is True
  assert module2.owns_bot is False

  assert len(created_bots) == 1
  bot = created_bots[0]
  assert bot.login_calls == 1
  assert bot.connect_calls == 1
  assert bot.wait_calls == 1

  asyncio.run(module2.on_ready())

  messages = [record.message for record in caplog.records]
  assert any("startup skipped" in msg for msg in messages)

  asyncio.run(module1.shutdown())
  asyncio.run(module2.shutdown())

