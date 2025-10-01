import asyncio, importlib.util, pathlib, sys, types
from dataclasses import dataclass
from typing import Callable, Iterable

from server.modules.providers import DBResult, DbRunMode
import server.modules.providers.database.mssql_provider  # ensure provider module loaded

root_path = pathlib.Path(__file__).resolve().parent.parent

# Stub package structure
server_pkg = types.ModuleType('server')
server_pkg.__path__ = [str(root_path / 'server')]
sys.modules.setdefault('server', server_pkg)
modules_pkg = types.ModuleType('server.modules')
modules_pkg.__path__ = [str(root_path / 'server/modules')]
sys.modules.setdefault('server.modules', modules_pkg)
providers_pkg = types.ModuleType('server.modules.providers')
providers_pkg.__path__ = [str(root_path / 'server/modules/providers')]
sys.modules.setdefault('server.modules.providers', providers_pkg)
database_pkg = types.ModuleType('server.modules.providers.database')
database_pkg.__path__ = [str(root_path / 'server/modules/providers/database')]
sys.modules.setdefault('server.modules.providers.database', database_pkg)
mssql_pkg = types.ModuleType('server.modules.providers.database.mssql_provider')
mssql_pkg.__path__ = [str(root_path / 'server/modules/providers/database/mssql_provider')]
sys.modules.setdefault('server.modules.providers.database.mssql_provider', mssql_pkg)

# Stub dependencies required by registry
logic_mod = types.ModuleType('server.modules.providers.database.mssql_provider.logic')
logic_mod.init_pool = lambda *args, **kwargs: None
logic_mod.close_pool = lambda *args, **kwargs: None
async def _dummy_tx():
  yield
logic_mod.transaction = lambda: _dummy_tx()
logic_mod._pool = object()
sys.modules['server.modules.providers.database.mssql_provider.logic'] = logic_mod


@dataclass(slots=True)
class Operation:
  kind: DbRunMode
  sql: str
  params: tuple = ()
  postprocess: Callable[[DBResult], DBResult] | None = None


def json_one(sql: str, params: Iterable = (), *, postprocess: Callable[[DBResult], DBResult] | None = None):
  return Operation(DbRunMode.JSON_ONE, sql, tuple(params), postprocess)


def json_many(sql: str, params: Iterable = (), *, postprocess: Callable[[DBResult], DBResult] | None = None):
  return Operation(DbRunMode.JSON_MANY, sql, tuple(params), postprocess)


def row_one(sql: str, params: Iterable = (), *, postprocess: Callable[[DBResult], DBResult] | None = None):
  return Operation(DbRunMode.ROW_ONE, sql, tuple(params), postprocess)


def row_many(sql: str, params: Iterable = (), *, postprocess: Callable[[DBResult], DBResult] | None = None):
  return Operation(DbRunMode.ROW_MANY, sql, tuple(params), postprocess)


def exec_op(sql: str, params: Iterable = (), *, postprocess: Callable[[DBResult], DBResult] | None = None):
  return Operation(DbRunMode.EXEC, sql, tuple(params), postprocess)


async def dummy_fetch_rows(*args, **kwargs):
  return DBResult()


async def dummy_fetch_json(operation: Operation):
  return DBResult(rows=[{'recid': 1}], rowcount=1)


async def dummy_exec_query(operation: Operation):
  return DBResult(rowcount=1)


async def execute_operation(operation: Operation):
  if operation.kind is DbRunMode.EXEC:
    return await dummy_exec_query(operation)
  return await dummy_fetch_json(operation)


helpers_mod = sys.modules['server.modules.providers.database.mssql_provider.db_helpers']
helpers_mod.fetch_rows = dummy_fetch_rows
helpers_mod.fetch_json = dummy_fetch_json
helpers_mod.exec_query = dummy_exec_query
helpers_mod.execute_operation = execute_operation
helpers_mod.logic._pool = True

spec = importlib.util.spec_from_file_location(
  'server.modules.providers.database.mssql_provider.registry',
  root_path / 'server/modules/providers/database/mssql_provider/registry.py',
)
registry_mod = importlib.util.module_from_spec(spec)
sys.modules['server.modules.providers.database.mssql_provider.registry'] = registry_mod
spec.loader.exec_module(registry_mod)

cache_mod = sys.modules['server.registry.content.cache.mssql']
cache_mod.fetch_json = dummy_fetch_json
cache_mod.exec_query = dummy_exec_query


def test_storage_cache_upsert_sets_created_on(monkeypatch):
  captured = []
  async def fake_exec_query(operation):
    captured.append(operation.params)
    return DBResult(rowcount=1)
  monkeypatch.setattr(cache_mod, 'exec_query', fake_exec_query)
  handler = registry_mod.get_handler('db:content:cache:upsert:1')
  args = {
  'user_guid': 'u',
  'path': '',
  'filename': 'file.txt',
  'content_type': 'text/plain',
  'public': 0,
  'created_on': None,
  'modified_on': None,
  'url': None,
  'reported': 0,
  'moderation_recid': None,
  }
  asyncio.run(handler(args))
  assert captured and captured[0][5] is not None
