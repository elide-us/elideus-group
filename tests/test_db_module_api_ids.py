import asyncio
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBResult


def test_get_google_client_id():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "GoogleClientId"}
    return DBResult(rows=[{"value": "gid"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_google_client_id()) == "gid"


def test_get_google_api_secret():
  app = FastAPI()
  db = DbModule(app)
  class DummyEnv:
    async def on_ready(self):
      return None
    def get(self, k):
      assert k == "GOOGLE_AUTH_SECRET"
      return "gsecret"
  app.state.env = DummyEnv()
  assert asyncio.run(db.get_google_api_secret()) == "gsecret"


def test_get_discord_client_id():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "DiscordClientId"}
    return DBResult(rows=[{"value": "dcid"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_discord_client_id()) == "dcid"


def test_get_ms_api_id():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "MsApiId"}
    return DBResult(rows=[{"value": "mid"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_ms_api_id()) == "mid"


def test_get_auth_providers():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "AuthProviders"}
    return DBResult(rows=[{"value": "microsoft,google,discord"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_auth_providers()) == ["microsoft", "google", "discord"]


def test_get_jwks_cache_time():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "JwksCacheTime"}
    return DBResult(rows=[{"value": "45"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_jwks_cache_time()) == 45

