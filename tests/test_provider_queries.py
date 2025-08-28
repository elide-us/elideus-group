from uuid import uuid4
import asyncio
import importlib.util
import pathlib
import sys
import types
import server.modules.providers.database.mssql_provider  # ensure provider module loaded

# stub server package
root_path = pathlib.Path(__file__).resolve().parent.parent
server_pkg = types.ModuleType("server")
server_pkg.__path__ = [str(root_path / "server")]
sys.modules.setdefault("server", server_pkg)
modules_pkg = types.ModuleType("server.modules")
modules_pkg.__path__ = [str(root_path / "server/modules")]
sys.modules.setdefault("server.modules", modules_pkg)
providers_pkg = types.ModuleType("server.modules.providers")
providers_pkg.__path__ = [str(root_path / "server/modules/providers")]
sys.modules.setdefault("server.modules.providers", providers_pkg)
database_pkg = types.ModuleType("server.modules.providers.database")
database_pkg.__path__ = [str(root_path / "server/modules/providers/database")]
sys.modules.setdefault("server.modules.providers.database", database_pkg)
mssql_pkg = types.ModuleType("server.modules.providers.database.mssql_provider")
mssql_pkg.__path__ = [str(root_path / "server/modules/providers/database/mssql_provider")]
sys.modules.setdefault("server.modules.providers.database.mssql_provider", mssql_pkg)

spec_logic = importlib.util.spec_from_file_location(
  "server.modules.providers.database.mssql_provider.logic",
  root_path / "server/modules/providers/database/mssql_provider/logic.py",
)
logic_mod = importlib.util.module_from_spec(spec_logic)
sys.modules["server.modules.providers.database.mssql_provider.logic"] = logic_mod
spec_logic.loader.exec_module(logic_mod)

spec_models = importlib.util.spec_from_file_location(
  "server.modules.providers.models",
  root_path / "server/modules/providers/models.py",
)
models_mod = importlib.util.module_from_spec(spec_models)
sys.modules["server.modules.providers.models"] = models_mod
spec_models.loader.exec_module(models_mod)

spec_db_helpers = importlib.util.spec_from_file_location(
  "server.modules.providers.database.mssql_provider.db_helpers",
  root_path / "server/modules/providers/database/mssql_provider/db_helpers.py",
)
db_helpers = importlib.util.module_from_spec(spec_db_helpers)
sys.modules["server.modules.providers.database.mssql_provider.db_helpers"] = db_helpers
spec_db_helpers.loader.exec_module(db_helpers)

spec_registry = importlib.util.spec_from_file_location(
  "server.modules.providers.database.mssql_provider.registry",
  root_path / "server/modules/providers/database/mssql_provider/registry.py",
)
registry_mod = importlib.util.module_from_spec(spec_registry)
sys.modules["server.modules.providers.database.mssql_provider.registry"] = registry_mod
spec_registry.loader.exec_module(registry_mod)
get_mssql_handler = registry_mod.get_handler

def test_mssql_get_by_provider_identifier_uses_user_view():
  handler = get_mssql_handler("urn:users:providers:get_by_provider_identifier:1")
  _, sql, _ = handler({"provider": "microsoft", "provider_identifier": str(uuid4())})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_profile_uses_profile_view():
  handler = get_mssql_handler("urn:users:profile:get_profile:1")
  _, sql, _ = handler({"guid": "gid"})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_rotkey_uses_security_view():
  handler = get_mssql_handler("db:users:session:get_rotkey:1")
  _, sql, _ = handler({"guid": "gid"})
  assert "vw_account_user_security" in sql.lower()

def test_mssql_get_by_access_token_uses_security_view():
  handler = get_mssql_handler("db:auth:session:get_by_access_token:1")
  _, sql, _ = handler({"access_token": "tok"})
  sql = sql.lower()
  assert "vw_account_user_security" in sql
  assert "providers_recid" in sql


def test_fetch_rows_returns_empty_on_error(monkeypatch):
  class Cur:
    async def execute(self, q, p):
      raise Exception("boom")

  class Conn:
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      return Conn()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.fetch_rows("SELECT 1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_fetch_json_returns_empty_on_error(monkeypatch):
  class Cur:
    async def execute(self, q, p):
      raise Exception("boom")
    async def fetchone(self):
      return None

  class Conn:
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      return Conn()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.fetch_json("SELECT 1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_exec_query_returns_empty_on_error(monkeypatch):
  class Cur:
    async def execute(self, q, p):
      raise Exception("boom")

  class Conn:
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      return Conn()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.exec_query("UPDATE x SET y=1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_fetch_rows_stream(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def execute(self, q, p):
      pass
    async def fetchone(self):
      return None

  class Conn:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()
        async def __aexit__(self_inner, exc_type, exc, tb):
          pass
      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())

  async def run():
    gen = await db_helpers.fetch_rows("SELECT", stream=True)
    return hasattr(gen, "__aiter__")

  assert asyncio.run(run())
