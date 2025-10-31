import asyncio
import logging
from textwrap import dedent

from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBRequest, DBResponse
from server.modules.registry.helpers import account_exists_request


class _StubHandlerInfo:
  legacy = False

  def __init__(self, handler):
    self._handler = handler
    self.load_called = False

  def load(self):
    self.load_called = True
    return self._handler


class _StubProvider:
  def __init__(self):
    self.run_called = False
    self.log_dispatch_calls = []
    self.await_handler_result_calls = []
    self.normalize_response_calls = []

  async def run(self, request):
    self.run_called = True
    return DBResponse(op=request.op, rows=[], rowcount=0)

  def log_dispatch(self, op):
    self.log_dispatch_calls.append(op)

  async def await_handler_result(self, result):
    self.await_handler_result_calls.append(result)
    return result

  def normalize_response(self, op, result):
    self.normalize_response_calls.append((op, result))
    return DBResponse(op=op, rows=result["rows"], rowcount=result.get("rowcount"))


class _LegacyInfo:
  legacy = True

  def load(self):  # pragma: no cover - guard to ensure it is never called
    raise AssertionError("Legacy handler should not be loaded")


class _LegacyProvider:
  def __init__(self):
    self.run_calls = []

  async def run(self, request):
    self.run_calls.append(request)
    return DBResponse(op=request.op, rows=[{"result": "legacy"}], rowcount=1)


def test_run_dispatches_registry_handler(monkeypatch):
  app = FastAPI()
  db = DbModule(app)
  provider = _StubProvider()
  db._provider = provider

  request = DBRequest(op="db:system:config:get_config:1", payload={"key": "LoggingLevel"})

  handler_result = {"rows": [{"value": "42"}], "rowcount": 1}
  handler_calls = []

  def handler(payload):
    handler_calls.append(payload)
    return handler_result

  info = _StubHandlerInfo(handler)

  def fake_get_handler_info(op, *, provider, log_resolution):
    assert op == request.op
    assert provider == db.provider == "mssql"
    assert log_resolution is False
    return info

  monkeypatch.setattr("server.modules.db_module.get_handler_info", fake_get_handler_info)

  async def run_scenario():
    response = await db.run(request)
    assert handler_calls == [request.payload]
    assert info.load_called is True
    assert provider.log_dispatch_calls == [request.op]
    assert provider.await_handler_result_calls == [handler_result]
    assert provider.normalize_response_calls == [(request.op, handler_result)]
    assert provider.run_called is False
    assert response.op == request.op
    assert response.rows == handler_result["rows"]
    assert response.rowcount == handler_result["rowcount"]

  asyncio.run(run_scenario())


def test_run_falls_back_to_provider_for_legacy_handlers(monkeypatch, caplog):
  app = FastAPI()
  db = DbModule(app)
  provider = _LegacyProvider()
  db._provider = provider

  request = DBRequest(op="db:legacy:operation:1", payload={"foo": "bar"})

  def fake_get_handler_info(op, *, provider, log_resolution):
    assert op == request.op
    assert provider == db.provider
    assert log_resolution is False
    return _LegacyInfo()

  monkeypatch.setattr("server.modules.db_module.get_handler_info", fake_get_handler_info)

  async def run_scenario():
    response = await db.run(request)
    assert provider.run_calls == [request]
    assert response.op == request.op
    assert response.rows == [{"result": "legacy"}]
    assert response.rowcount == 1

  with caplog.at_level(logging.WARNING, logger="server.registry"):
    asyncio.run(run_scenario())

  fallback_logs = [
    record
    for record in caplog.records
    if record.name == "server.registry" and record.levelno == logging.WARNING
  ]
  assert any("Registry handler fallback triggered" in record.message for record in fallback_logs)
  assert any(record.db_op == request.op for record in fallback_logs)
  assert any(record.db_provider == db.provider for record in fallback_logs)


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


def test_user_exists_falls_back_when_registry_missing(monkeypatch):
  app = FastAPI()
  db = DbModule(app)

  async def fake_exists(args):
    assert args == {"user_guid": "guid-123"}
    return DBResponse(rows=[{"exists_flag": 1}], rowcount=1)

  def fake_try_get_handler_info(op, *, provider):
    assert op == "db:account:accounts:exists:1"
    assert provider == db.provider
    return None

  async def fake_run(_request):
    raise AssertionError("DbModule.run should not be called when fallback is used")

  monkeypatch.setattr("server.modules.db_module.try_get_handler_info", fake_try_get_handler_info)
  monkeypatch.setattr(
    "server.registry.account.accounts.mssql.account_exists_v1",
    fake_exists,
  )
  monkeypatch.setattr(db, "run", fake_run)

  async def run_scenario():
    result = await db.user_exists("guid-123")
    assert result is True

  asyncio.run(run_scenario())


def test_run_uses_registry_account_exists_handler(monkeypatch):
  app = FastAPI()
  db = DbModule(app)

  class _PassThroughProvider:
    def __init__(self):
      self.log_dispatch_calls = []

    def log_dispatch(self, op):
      self.log_dispatch_calls.append(op)

  provider = _PassThroughProvider()
  db._provider = provider

  db_response = DBResponse(
    op="db:account:accounts:exists:1",
    rows=[{"exists_flag": 1}],
    rowcount=1,
  )
  run_calls = []

  async def fake_run_json_one(sql, params):
    run_calls.append((sql, params))
    return db_response

  monkeypatch.setattr(
    "server.registry.account.accounts.mssql.run_json_one",
    fake_run_json_one,
  )

  request = account_exists_request("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

  async def run_scenario():
    response = await db.run(request)
    assert response is db_response

  asyncio.run(run_scenario())

  assert len(run_calls) == 1
  sql, params = run_calls[0]
  expected_sql = dedent(
    """
    SELECT 1 AS exists_flag
    FROM account_users
    WHERE element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
  ).strip()
  assert dedent(sql).strip() == expected_sql
  assert params == ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",)
