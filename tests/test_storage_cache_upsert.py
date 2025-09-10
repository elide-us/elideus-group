import asyncio, importlib.util, pathlib, sys, types
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
sys.modules['server.modules.providers.database.mssql_provider.logic'] = logic_mod

helpers_mod = types.ModuleType('server.modules.providers.database.mssql_provider.db_helpers')
async def dummy_fetch_rows(*args, **kwargs):
  return None
async def dummy_fetch_json(*args, **kwargs):
  return types.SimpleNamespace(rows=[{'recid': 1}], rowcount=1)
async def dummy_exec_query(*args, **kwargs):
  return types.SimpleNamespace(rowcount=1)
helpers_mod.fetch_rows = dummy_fetch_rows
helpers_mod.fetch_json = dummy_fetch_json
helpers_mod.exec_query = dummy_exec_query
sys.modules['server.modules.providers.database.mssql_provider.db_helpers'] = helpers_mod

spec = importlib.util.spec_from_file_location(
  'server.modules.providers.database.mssql_provider.registry',
  root_path / 'server/modules/providers/database/mssql_provider/registry.py',
)
registry_mod = importlib.util.module_from_spec(spec)
sys.modules['server.modules.providers.database.mssql_provider.registry'] = registry_mod
spec.loader.exec_module(registry_mod)


def test_storage_cache_upsert_sets_created_on(monkeypatch):
  captured = []
  async def fake_exec_query(sql, params):
    captured.append(params)
    return types.SimpleNamespace(rowcount=1)
  monkeypatch.setattr(registry_mod, 'exec_query', fake_exec_query)
  handler = registry_mod.get_handler('db:storage:cache:upsert:1')
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
