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
from server.registry.users.profile import mssql as users_profile_mssql


def _install_stub_provider(monkeypatch, name: str, queries: dict[str, Any]) -> str:
  module_name = f"server.registry.providers.{name}"
  module = ModuleType(module_name)
  module.PROVIDER_QUERIES = queries
  monkeypatch.setitem(sys.modules, module_name, module)
  return name


class _NoopProvider(DbProviderBase):
  async def startup(self):
    pass

  async def shutdown(self):
    pass

  async def run(self, op, args=None):
    raise AssertionError("provider.run should not be invoked in tests")


class _StubRegistryRouter(RegistryRouter):
  def register_domains(self) -> None:
    if not getattr(self, "_initialised", False):
      self._initialised = True


def test_init_uses_concrete_provider():
  app = FastAPI()
  db = DbModule(app)
  asyncio.run(db.init(provider="mssql"))
  assert isinstance(db._provider, MssqlProvider)


def test_db_module_run_propagates_query_error(monkeypatch):
  app = FastAPI()
  db = DbModule(app)
  detail = QueryErrorDetail(query="SELECT 1", params=(), message="boom")

  router = _StubRegistryRouter()
  router.domain("test").subdomain("error").add_function(
    "trigger",
    version=1,
    provider_map="test.error.trigger",
  )

  async def failing_callable(request: DBRequest) -> DBResponse:
    raise DBQueryError(detail)

  provider_name = _install_stub_provider(
    monkeypatch,
    "stub_error",
    {"test.error.trigger": {1: failing_callable}},
  )

  provider = _NoopProvider()
  db._provider = provider
  registry = RegistryDispatcher(router=router)
  registry.bind_provider(provider, provider_name=provider_name)
  db.set_registry(registry)

  with pytest.raises(DBQueryError) as exc:
    asyncio.run(db.run(DBRequest(op="db:test:error:trigger:1", params={})))
  assert exc.value.detail == detail


def test_db_module_forwards_operations_verbatim(monkeypatch):
  app = FastAPI()
  db = DbModule(app)
  captured: dict[str, Any] = {}

  router = _StubRegistryRouter()
  router.domain("test").subdomain("ops").add_function(
    "urn_op",
    version=1,
    provider_map="test.ops.urn_op",
  )

  async def recording_callable(request: DBRequest) -> DBResponse:
    captured["op"] = request.op
    captured["args"] = request.params
    return DBResponse(rows=[{"ok": True}], rowcount=1)

  provider_name = _install_stub_provider(
    monkeypatch,
    "stub_record",
    {"test.ops.urn_op": {1: recording_callable}},
  )

  provider = _NoopProvider()
  db._provider = provider
  registry = RegistryDispatcher(router=router)
  registry.bind_provider(provider, provider_name=provider_name)
  db.set_registry(registry)

  result = asyncio.run(
    db.run(DBRequest(op="db:test:ops:urn_op:1", params={"foo": "bar"}))
  )
  assert captured["op"] == "db:test:ops:urn_op:1"
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
  router = _StubRegistryRouter()
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

  provider_name = _install_stub_provider(
    monkeypatch,
    "stub",
    {"demo.ops.test": {1: stub_callable}},
  )

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
  dispatcher.bind_provider(DummyProvider(), provider_name=provider_name)

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

  router.provider_bindings["db:demo:ops:missing:1"].descriptor = None

  with pytest.raises(ValueError, match="does not declare a provider binding"):
    router.load_provider("mssql")


def test_dispatcher_raises_for_unknown_operation(monkeypatch):
  dispatcher = RegistryDispatcher(router=_StubRegistryRouter())
  provider = _NoopProvider()
  provider_name = _install_stub_provider(monkeypatch, "stub_unknown", {})
  dispatcher.bind_provider(provider, provider_name=provider_name)

  with pytest.raises(KeyError, match="Unknown registry operation"):
    asyncio.run(
      dispatcher.execute(DBRequest(op="db:test:missing:op:1", params={}))
    )


def test_provider_startup_checks_missing_callable(monkeypatch):
  router = _StubRegistryRouter()
  router.domain("demo").subdomain("ops").add_function(
    "missing",
    version=1,
    provider_map="demo.ops.missing",
  )

  provider = _NoopProvider()
  provider_name = _install_stub_provider(monkeypatch, "stub_incomplete", {})
  dispatcher = RegistryDispatcher(router=router)

  with pytest.raises(RuntimeError) as exc:
    dispatcher.bind_provider(provider, provider_name=provider_name)

  assert "db:demo:ops:missing:1" in str(exc.value)


def test_accounts_profile_routes_resolve_wrappers(monkeypatch):
  router = RegistryRouter()
  router.register_domains()

  route = router.resolve("db:accounts:profile:get_profile:1")
  assert route is not None
  assert route.provider_map == "accounts.profile.get_profile"

  binding = router.provider_bindings[route.key]
  assert binding.descriptor == (
    "server.registry.accounts.profile.mssql",
    "get_profile_v1",
  )

  captured: dict[str, Any] = {}

  async def fake_get_profile(args: dict[str, Any]) -> DBResponse:
    captured["args"] = args
    return DBResponse(rows=[{"ok": True}], rowcount=1)

  monkeypatch.setattr(users_profile_mssql, "get_profile_v1", fake_get_profile)

  router.load_provider("mssql")
  executor = router.get_executor(route)

  request = DBRequest(op=route.key, params={"guid": "gid"})
  response = asyncio.run(executor(request))

  assert response.rows == [{"ok": True}]
  assert captured["args"] == {"guid": "gid"}
