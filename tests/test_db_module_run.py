import asyncio
import uuid

from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBResponse

def test_user_exists_dispatches_exists_handler(monkeypatch):
  app = FastAPI()
  db = DbModule(app)

  requests = []

  async def fake_dispatch(request, *, provider):
    requests.append(request)
    return DBResponse(op=request.op, payload={"exists_flag": 1})

  monkeypatch.setattr("server.modules.db_module.dispatch_query_request", fake_dispatch)

  user_guid = str(uuid.uuid4())

  async def run_scenario():
    result = await db.user_exists(user_guid)
    assert result is True

  asyncio.run(run_scenario())

  assert requests, "DbModule.user_exists should dispatch a DB request"
  request = requests[0]
  assert request.op == "db:identity:accounts:exists:1"
  assert request.payload == {"user_guid": user_guid}
