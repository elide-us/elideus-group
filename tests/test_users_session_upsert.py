import asyncio, importlib.util, pathlib, sys, types
from contextlib import asynccontextmanager
from datetime import datetime, timezone

root_path = pathlib.Path(__file__).resolve().parent.parent

# Stub package structure
server_pkg = types.ModuleType("server")
server_pkg.__path__ = [str(root_path / "server")]
sys.modules.setdefault("server", server_pkg)
modules_pkg = types.ModuleType("server.modules")
modules_pkg.__path__ = [str(root_path / "server/modules")]
sys.modules.setdefault("server.modules", modules_pkg)
providers_pkg = types.ModuleType("server.modules.providers")
providers_pkg.__path__ = [str(root_path / "server/modules/providers")]
sys.modules.setdefault("server.modules.providers", providers_pkg)
mssql_pkg = types.ModuleType("server.modules.providers.mssql_provider")
mssql_pkg.__path__ = [str(root_path / "server/modules/providers/mssql_provider")]
sys.modules.setdefault("server.modules.providers.mssql_provider", mssql_pkg)

# Stub dependencies
a = types.ModuleType("server.modules.providers.mssql_provider.logic")
sys.modules["server.modules.providers.mssql_provider.logic"] = a
a.init_pool = lambda *args, **kwargs: None
a.close_pool = lambda *args, **kwargs: None
async def _dummy_tx():
  yield

a.transaction = lambda: _dummy_tx()

b = types.ModuleType("server.modules.providers.mssql_provider.db_helpers")
sys.modules["server.modules.providers.mssql_provider.db_helpers"] = b
b.fetch_rows = lambda *args, **kwargs: None
b.fetch_json = lambda *args, **kwargs: None
b.exec_query = lambda *args, **kwargs: None

spec = importlib.util.spec_from_file_location(
  "server.modules.providers.mssql_provider.registry",
  root_path / "server/modules/providers/mssql_provider/registry.py",
)
registry_mod = importlib.util.module_from_spec(spec)
sys.modules["server.modules.providers.mssql_provider.registry"] = registry_mod
spec.loader.exec_module(registry_mod)


def test_create_session_updates_existing(monkeypatch):
  executed: list[str] = []

  class DummyCur:
    async def execute(self, sql, params):
      executed.append(sql.lower())
    async def fetchone(self):
      return {"element_guid": "sess"}

  @asynccontextmanager
  async def fake_tx():
    yield DummyCur()

  monkeypatch.setattr(registry_mod, "transaction", fake_tx)
  handler = registry_mod.get_handler("db:auth:session:create_session:1")
  args = {
    "access_token": "tok",
    "expires": datetime.now(timezone.utc),
    "fingerprint": None,
    "user_agent": None,
    "ip_address": None,
    "user_guid": "user",
  }
  asyncio.run(handler(args))
  assert any("update users_sessions" in q for q in executed)
  assert not any("insert into users_sessions" in q for q in executed)
