import pytest
import asyncio
from fastapi import FastAPI
from types import SimpleNamespace
import server.modules.database_module as db_mod
from server.modules.database_module import DatabaseModule
from server.modules.env_module import EnvironmentModule

@pytest.fixture
def db_app(monkeypatch):
  monkeypatch.setenv("VERSION", "1")
  monkeypatch.setenv("HOSTNAME", "host")
  monkeypatch.setenv("REPO", "repo")
  monkeypatch.setenv("DISCORD_SECRET", "secret")
  monkeypatch.setenv("DISCORD_SYSCHAN", "1")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("MS_API_ID", "msid")
  monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgres://user@host/db")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  app.state.discord = SimpleNamespace()
  return app

def test_db_startup(monkeypatch, db_app):
  async def fake_pool(**kwargs):
    return "pool"
  monkeypatch.setattr(db_mod.asyncpg, "create_pool", fake_pool)
  dbm = DatabaseModule(db_app)
  asyncio.run(dbm.startup())
  assert dbm.pool == "pool"

def test_db_fetch_one_without_pool(db_app):
  dbm = DatabaseModule(db_app)
  with pytest.raises(RuntimeError):
    asyncio.run(dbm._fetch_one("SELECT 1"))
