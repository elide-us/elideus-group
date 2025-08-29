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

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "GoogleApiId"}
    return DBResult(rows=[{"value": "gsecret"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_google_api_secret()) == "gsecret"


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
    return DBResult(rows=[{"value": "microsoft,google"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_auth_providers()) == ["microsoft", "google"]


def test_get_jwks_cache_time():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "JwksCacheTime"}
    return DBResult(rows=[{"value": "45"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_jwks_cache_time()) == 45

