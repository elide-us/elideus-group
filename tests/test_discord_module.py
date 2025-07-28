import pytest
import asyncio
from fastapi import FastAPI
from types import SimpleNamespace
import server.modules.discord_module as discord_mod
from server.modules.env_module import EnvironmentModule
from server.modules.discord_module import DiscordModule
from server.helpers.logging import MAX_DISCORD_MESSAGE_LEN

class DummyBot:
  def __init__(self):
    self.loop = asyncio.new_event_loop()
  def start(self, secret):
    self.started = secret
  def get_channel(self, chan):
    return None
  def event(self, fn):
    return fn
  def command(self, name=None):
    def decorator(fn):
      self.cmd = fn
      return fn
    return decorator

@pytest.fixture
def discord_app(monkeypatch):
  monkeypatch.setenv("VERSION", "1")
  monkeypatch.setenv("HOSTNAME", "host")
  monkeypatch.setenv("REPO", "repo")
  monkeypatch.setenv("DISCORD_SECRET", "secret")
  monkeypatch.setenv("DISCORD_SYSCHAN", "1")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "cs")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  class DB:
    async def get_config_value(self, key):
      if key == "DiscordSyschan":
        return "1"
      if key == "Hostname":
        return "host"
      if key == "Version":
        return "v1.2.3"
  app.state.mssql = DB()
  return app

def test_discord_module_init(monkeypatch, discord_app):
  monkeypatch.setattr(discord_mod, "configure_discord_logging", lambda m: None)
  monkeypatch.setattr(discord_mod.asyncio, "create_task", lambda coro: None)
  monkeypatch.setattr(DiscordModule, "_init_bot_routes", lambda self: None)
  monkeypatch.setattr(DiscordModule, "_init_discord_bot", lambda self, p: DummyBot())
  mod = DiscordModule(discord_app)
  asyncio.run(mod.startup())
  assert mod.secret == "secret"
  assert mod.syschan == 1
  assert isinstance(mod.bot, DummyBot)

def test_discord_module_missing_env():
  app = FastAPI()
  with pytest.raises(Exception):
    DiscordModule(app)

class Chan:
  def __init__(self):
    self.messages = []
  async def send(self, msg):
    self.messages.append(msg)

def _setup(monkeypatch, discord_app, chan=None):
  monkeypatch.setattr(discord_mod, "configure_discord_logging", lambda m: None)
  monkeypatch.setattr(discord_mod.asyncio, "create_task", lambda coro: None)
  monkeypatch.setattr(DiscordModule, "_init_bot_routes", lambda self: None)
  def _make_bot(self, p):
    bot = DummyBot()
    bot.get_channel = lambda c: chan
    return bot
  monkeypatch.setattr(DiscordModule, "_init_discord_bot", _make_bot)
  mod = DiscordModule(discord_app)
  asyncio.run(mod.startup())
  return mod

def test_send_sys_message(monkeypatch, discord_app):
  chan = Chan()
  mod = _setup(monkeypatch, discord_app, chan)
  asyncio.run(mod.send_sys_message("hi"))
  assert chan.messages == ["hi"]

def test_send_sys_message_no_channel(monkeypatch, discord_app):
  mod = _setup(monkeypatch, discord_app, None)
  asyncio.run(mod.send_sys_message("hi"))

def test_send_sys_message_long(monkeypatch, discord_app):
  chan = Chan()
  mod = _setup(monkeypatch, discord_app, chan)
  long_msg = "a" * 3000
  asyncio.run(mod.send_sys_message(long_msg))
  assert chan.messages == ["a" * MAX_DISCORD_MESSAGE_LEN, "a" * (3000 - MAX_DISCORD_MESSAGE_LEN)]


def test_rpc_command(monkeypatch, discord_app):
  messages = []

  def _make_bot(self, p):
    bot = DummyBot()
    bot.get_channel = lambda c: None
    return bot

  monkeypatch.setattr(discord_mod, "configure_discord_logging", lambda m: None)
  monkeypatch.setattr(discord_mod.asyncio, "create_task", lambda coro: None)
  monkeypatch.setattr(DiscordModule, "_init_discord_bot", _make_bot)

  mod = DiscordModule(discord_app)
  asyncio.run(mod.startup())

  class Ctx:
    async def send(self, m):
      messages.append(m)

  ctx = Ctx()
  asyncio.run(mod.bot.cmd(ctx, op="urn:frontend:vars:get_hostname:2"))

  assert messages == ['{"hostname": "host"}']


def test_on_ready_reports_version(monkeypatch, discord_app):
  chan = Chan()

  def _make_bot(self, p):
    bot = DummyBot()
    bot.get_channel = lambda c: chan
    def event(fn):
      setattr(bot, fn.__name__, fn)
      return fn
    bot.event = event
    return bot

  monkeypatch.setattr(discord_mod, 'configure_discord_logging', lambda m: None)
  monkeypatch.setattr(discord_mod.asyncio, 'create_task', lambda coro: None)
  monkeypatch.setattr(DiscordModule, '_init_discord_bot', _make_bot)

  mod = DiscordModule(discord_app)
  asyncio.run(mod.startup())
  asyncio.run(mod.bot.on_ready())

  assert chan.messages == ['TheOracleRPC Online. Version: v1.2.3']

