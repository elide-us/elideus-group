import asyncio
from typing import Any
import pytest
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DBResult, DbProviderBase
from server.modules.providers.database.mssql_provider import MssqlProvider
from server.modules.providers.database.mssql_provider.db_helpers import DBQueryError, QueryErrorDetail
from server.registry import RegistryDispatcher
from server.registry.types import DBResponse


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

    async def run(self, op, args):
      raise DBQueryError(detail)

  db._provider = FailingProvider()
  registry = RegistryDispatcher()
  registry.bind_provider(db._provider)
  db.set_registry(registry)

  with pytest.raises(DBQueryError) as exc:
    asyncio.run(db.run("db:test:error", {}))
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

    async def run(self, op, args):
      captured["op"] = op
      captured["args"] = args
      return DBResult(rows=[{"ok": True}], rowcount=1)

  db._provider = RecordingProvider()
  registry = RegistryDispatcher()
  registry.bind_provider(db._provider)
  db.set_registry(registry)

  result = asyncio.run(db.run("db:test:urn-op:1", {"foo": "bar"}))
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

    async def run(self, op, args):
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

  result = asyncio.run(db.run("db:test:op", {"key": "value"}))

  assert result.rows == [{"ok": True}]
  assert result.rowcount == 1
  assert len(registry.requests) == 1
  request = registry.requests[0]
  assert request.op == "db:test:op"
  assert request.params == {"key": "value"}
