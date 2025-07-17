import asyncio
from fastapi import FastAPI
import server.modules.discord_module as discord_mod
import server.modules.database_module as db_mod
import server.modules.auth_module as auth_mod
from server.modules.discord_module import DiscordModule
from server.lifespan import lifespan

class DummyBot:
  def __init__(self):
    self.loop = asyncio.new_event_loop()
  def start(self, secret):
    self.started = secret
  def get_channel(self, chan):
    return None
  def event(self, fn):
    return fn


def test_lifespan_initializes_modules(monkeypatch):
  monkeypatch.setenv("DISCORD_SECRET", "secret")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgres://user@host/db")

  monkeypatch.setattr(discord_mod, "configure_discord_logging", lambda m: None)
  monkeypatch.setattr(discord_mod.asyncio, "create_task", lambda coro: None)
  monkeypatch.setattr(DiscordModule, "_init_bot_routes", lambda self: None)
  monkeypatch.setattr(DiscordModule, "_init_discord_bot", lambda self, p: DummyBot())

  async def fake_pool(**kwargs):
    return "pool"
  monkeypatch.setattr(db_mod.asyncpg, "create_pool", fake_pool)

  async def fake_get_config(self, key):
    if key == "DiscordSyschan":
      return "1"
    return "0"
  monkeypatch.setattr(db_mod.DatabaseModule, "get_config_value", fake_get_config)

  async def fake_uri():
    return "url"
  async def fake_jwks(uri):
    return {"keys": []}
  monkeypatch.setattr(auth_mod, "fetch_ms_jwks_uri", fake_uri)
  monkeypatch.setattr(auth_mod, "fetch_ms_jwks", fake_jwks)
  async def fake_startup(self):
    return None
  monkeypatch.setattr(auth_mod.AuthModule, "startup", fake_startup)

  app = FastAPI()

  async def run():
    async with lifespan(app):
      assert app.state.env is not None
      assert app.state.discord is not None
      assert app.state.database is not None
      assert app.state.auth is not None

  asyncio.run(run())
