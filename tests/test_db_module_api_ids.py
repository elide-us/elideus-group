import asyncio
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBResponse
from server.registry.models import DBRequest


def test_get_google_client_id():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(request):
    assert isinstance(request, DBRequest)
    assert request.op == "db:system:config:get_config:1"
    assert request.payload == {"key": "GoogleClientId"}
    return DBResponse(rows=[{"value": "gid"}], rowcount=1)

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

  async def fake_run(request):
    assert isinstance(request, DBRequest)
    assert request.op == "db:system:config:get_config:1"
    assert request.payload == {"key": "DiscordClientId"}
    return DBResponse(rows=[{"value": "dcid"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_discord_client_id()) == "dcid"


def test_get_ms_api_id():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(request):
    assert isinstance(request, DBRequest)
    assert request.op == "db:system:config:get_config:1"
    assert request.payload == {"key": "MsApiId"}
    return DBResponse(rows=[{"value": "mid"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_ms_api_id()) == "mid"


def test_get_auth_providers():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(request):
    assert isinstance(request, DBRequest)
    assert request.op == "db:system:config:get_config:1"
    assert request.payload == {"key": "AuthProviders"}
    return DBResponse(rows=[{"value": "microsoft,google,discord"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_auth_providers()) == ["microsoft", "google", "discord"]


def test_get_jwks_cache_time():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(request):
    assert isinstance(request, DBRequest)
    assert request.op == "db:system:config:get_config:1"
    assert request.payload == {"key": "JwksCacheTime"}
    return DBResponse(rows=[{"value": "45"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_jwks_cache_time()) == 45

