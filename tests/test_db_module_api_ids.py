import asyncio
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers.models import DBResult


def test_get_google_api_id():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "GoogleApiId"}
    return DBResult(rows=[{"value": "gid"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_google_api_id()) == "gid"


def test_get_ms_api_id():
  app = FastAPI()
  db = DbModule(app)

  async def fake_run(op, args):
    assert op == "db:system:config:get_config:1"
    assert args == {"key": "MsApiId"}
    return DBResult(rows=[{"value": "mid"}], rowcount=1)

  db.run = fake_run
  assert asyncio.run(db.get_ms_api_id()) == "mid"

