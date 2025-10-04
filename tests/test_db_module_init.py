import asyncio
import sys
from types import ModuleType
from typing import Any
import pytest
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBResult, DbProviderBase
from server.modules.providers.database.mssql_provider import MssqlProvider
from server.modules.providers.database.mssql_provider.db_helpers import DBQueryError, QueryErrorDetail
from server.registry import RegistryDispatcher, RegistryRouter
from server.registry.types import DBRequest, DBResponse


def test_init_uses_concrete_provider():
  app = FastAPI()
  db = DbModule(app)
  asyncio.run(db.init(provider="mssql"))
  assert isinstance(db._provider, MssqlProvider)


def test_db_module_run_propagates_query_error():
  app = FastAPI()
  db = DbModule(app)
  detail = QueryErrorDetail(query="SELECT 1", params=(), message="boom")

  class FailingProvider(DbProviderBase):
    def __init__(self):
      super().__init__()

    async def startup(self):
      pass

    async def shutdown(self):
      pass

    async def run(self, op, args=None):
      if isinstance(op, DBRequest):
        args = op.params
        op = op.op
      args = args or {}
      raise DBQueryError(detail)

  db._provider = FailingProvider()
  registry = RegistryDispatcher()
  registry.bind_provider(db._provider)
  db.set_registry(registry)

  with pytest.raises(DBQueryError) as exc:
    asyncio.run(db.run(DBRequest(op="db:test:error:trigger:1", params={})))
  assert exc.value.detail == detail


def test_db_module_forwards_operations_verbatim():
  app = FastAPI()
  db = DbModule(app)
  captured: dict[str, Any] = {}

  class RecordingProvider(DbProviderBase):
    def __init__(self):
      super().__init__()

    async def startup(self):
      pass

    async def shutdown(self):
      pass

    async def run(self, op, args=None):
      if isinstance(op, DBRequest):
        args = op.params
        op = op.op
      args = args or {}
      captured["op"] = op
      captured["args"] = args
      return DBResult(rows=[{"ok": True}], rowcount=1)

  db._provider = RecordingProvider()
  registry = RegistryDispatcher()
  registry.bind_provider(db._provider)
  db.set_registry(registry)

  result = asyncio.run(db.run(DBRequest(op="db:test:urn-op:1", params={"foo": "bar"})))
  assert captured["op"] == "db:test:urn-op:1"
  assert captured["args"] == {"foo": "bar"}
  assert isinstance(result, DBResult)
  assert result.rows == [{"ok": True}]
  assert result.rowcount == 1


def test_db_module_run_constructs_registry_request():
  app = FastAPI()
  db = DbModule(app)

  class DummyProvider(DbProviderBase):
    async def startup(self):
      pass

    async def shutdown(self):
      pass

    async def run(self, op, args=None):
      if isinstance(op, DBRequest):
        args = op.params
        op = op.op
      args = args or {}
      raise AssertionError("provider should not be invoked in this test")

  class RecordingRegistry(RegistryDispatcher):
    def __init__(self):
      super().__init__()
      self.requests: list = []

    async def execute(self, request):
      self.requests.append(request)
      return DBResponse(rows=[{"ok": True}], rowcount=1)

  provider = DummyProvider()
  db._provider = provider
  registry = RecordingRegistry()
  db.set_registry(registry)

  result = asyncio.run(db.run(DBRequest(op="db:test:ops:trigger:1", params={"key": "value"})))

  assert result.rows == [{"ok": True}]
  assert result.rowcount == 1
  assert len(registry.requests) == 1
  request = registry.requests[0]
  assert request.op == "db:test:ops:trigger:1"
  assert request.params == {"key": "value"}


def test_registry_dispatcher_executes_provider_callable(monkeypatch):
  router = RegistryRouter()
  router.domain("demo").subdomain("ops").add_function(
    "test",
    version=1,
    provider_map="demo.ops.test",
  )

  calls: dict[str, Any] = {}

  async def stub_callable(request: DBRequest) -> DBResponse:
    calls["op"] = request.op
    calls["params"] = request.params
    value = request.params.get("value")
    return DBResponse(rows=[{"value": value}], rowcount=1)

  module = ModuleType("server.registry.providers.stub")
  module.PROVIDER_QUERIES = {
    "demo.ops.test": {1: stub_callable},
  }
  monkeypatch.setitem(sys.modules, module.__name__, module)

  class DummyProvider(DbProviderBase):
    async def startup(self):
      pass

    async def shutdown(self):
      pass

    async def run(self, op, args=None):
      if isinstance(op, DBRequest):
        args = op.params
        op = op.op
      args = args or {}
      raise AssertionError("provider.run should not be used when route is registered")

  dispatcher = RegistryDispatcher(router=router)
  dispatcher.bind_provider(DummyProvider(), provider_name="stub")

  response = asyncio.run(dispatcher.execute(DBRequest(op="db:demo:ops:test:1", params={"value": 7})))

  assert response.rows == [{"value": 7}]
  assert response.rowcount == 1
  assert calls["op"] == "db:demo:ops:test:1"
  assert calls["params"] == {"value": 7}


def test_mssql_provider_requires_binding():
  router = RegistryRouter()
  router.domain("demo").subdomain("ops").add_function(
    "missing",
    version=1,
    provider_map="demo.ops.missing",
  )

  with pytest.raises(ValueError, match="does not declare a provider binding"):
    router.load_provider("mssql")
