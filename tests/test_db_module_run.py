import asyncio

from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBRequest, DBResponse


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


def test_run_falls_back_to_provider_for_legacy_handlers(monkeypatch):
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

  asyncio.run(run_scenario())
