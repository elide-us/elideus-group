import asyncio

from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBResponse

def test_user_exists_dispatches_exists_handler(monkeypatch):
  app = FastAPI()
  db = DbModule(app)

  requests = []

  async def fake_run(request):
    requests.append(request)
    return DBResponse(op=request.op, rows=[{"result": True}], rowcount=1)

  monkeypatch.setattr(db, "run", fake_run)

  async def run_scenario():
    result = await db.user_exists("guid-123")
    assert result is True

  asyncio.run(run_scenario())

  assert requests, "DbModule.user_exists should dispatch a DB request"
  request = requests[0]
  assert request.op == "db:account:accounts:exists:1"
  assert request.payload == {"user_guid": "guid-123"}
