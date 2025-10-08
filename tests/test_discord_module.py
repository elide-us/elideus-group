import asyncio, logging
from fastapi import FastAPI
from server.registry.types import DBRequest

from server.modules import BaseModule
from server.modules.discord_bot_module import DiscordBotModule


class DummyEnv(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self._env = {
      "DISCORD_SECRET": "secret",
      "DISCORD_RPC_BASE_URL": "https://api.example.com",
      "DISCORD_RPC_TOKEN": "token",
      "DISCORD_RPC_SIGNING_SECRET": "signing",
    }

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

  async def run(self, op, args=None):
    if isinstance(op, DBRequest):
      args = op.params
      op = op.op
    args = args or {}
    class Res:
      def __init__(self, rows):
        self.rows = rows
        self.rowcount = len(rows)
    if op == "db:system:config:get_config:1":
      key = args.get("key")
      if key == "DiscordSyschan":
        return Res([{ "value": "123" }])
      if key == "DiscordRpcBaseUrl":
        return Res([{ "value": "https://api.example.com" }])
      if key == "DiscordRpcToken":
        return Res([{ "value": "token" }])
      if key == "DiscordRpcSigningSecret":
        return Res([{ "value": "signing" }])
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
  
  def fake_release(self):
      self._lock_handle = None

  monkeypatch.setattr(DiscordBotModule, "_init_discord_bot", fake_init)
  monkeypatch.setattr(DiscordBotModule, "_try_lock_file", fake_try_lock)

  module1 = DiscordBotModule(app)
  module2 = DiscordBotModule(app)

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

  monkeypatch.setattr(DiscordBotModule, "_release_bot_lock", fake_release)

  asyncio.run(module1.shutdown())
  asyncio.run(module2.shutdown())

