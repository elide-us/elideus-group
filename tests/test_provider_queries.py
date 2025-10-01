from uuid import uuid4
import asyncio
import importlib.util
import pathlib
import sys
import types
import pytest
from server.modules.providers import DbRunMode
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
  handler = get_mssql_handler("db:users:providers:get_by_provider_identifier:1")
  op = handler({"provider": "microsoft", "provider_identifier": str(uuid4())})
  assert hasattr(op, "sql")
  sql = op.sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_profile_uses_profile_view():
  handler = get_mssql_handler("db:users:profile:get_profile:1")
  op = handler({"guid": "gid"})
  assert hasattr(op, "sql")
  sql = op.sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

_SECURITY_PROFILE_CASES = [
  ({"guid": "gid"}, ("vw_user_session_security", "auth_providers"), False),
  (
    {"access_token": "tok"},
    ("vw_user_session_security", "user_roles", "auth_providers"),
    False,
  ),
  ({"discord_id": "42"}, ("vw_user_session_security", "auth_providers"), True),
  (
    {"provider": "discord", "provider_identifier": str(uuid4())},
    ("vw_user_session_security", "auth_providers"),
    True,
  ),
]


@pytest.mark.parametrize(
  ("args", "expected_fragments", "joins_users_auth"),
  _SECURITY_PROFILE_CASES,
)
def test_mssql_accounts_security_profile_routes_through_security_view(args, expected_fragments, joins_users_auth):
  handler = get_mssql_handler("db:accounts:security:get_security_profile:1")
  op = handler(args)
  assert hasattr(op, "sql")
  sql = op.sql.lower()
  for fragment in expected_fragments:
    assert fragment in sql
  assert ("join users_auth" in sql) is joins_users_auth


_REMOVED_SECURITY_URNS = [
  "db:auth:discord:get_security:1",
  "db:auth:session:get_by_access_token:1",
  "db:users:profile:get_roles:1",
  "db:users:session:get_rotkey:1",
]


@pytest.mark.parametrize("urn", _REMOVED_SECURITY_URNS)
def test_removed_security_aliases_are_not_registered(urn):
  with pytest.raises(KeyError):
    get_mssql_handler(urn)


def test_mssql_support_users_set_credits_updates_table():
  handler = get_mssql_handler("db:support:users:set_credits:1")
  op = handler({"guid": "gid", "credits": 10})
  assert hasattr(op, "sql")
  assert op.kind is DbRunMode.EXEC
  assert "update users_credits" in op.sql.lower()
  assert op.params == (10, "gid")


def test_fetch_rows_raises_structured_error(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def execute(self, q, p):
      raise Exception("boom")
    async def fetchone(self):
      return None

  class Conn:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()
        async def __aexit__(self_inner, exc_type, exc, tb):
          pass
      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  with pytest.raises(db_helpers.DBQueryError) as exc:
    asyncio.run(db_helpers.fetch_rows(db_helpers.row_one("SELECT 1")))
  assert exc.value.detail.query == "SELECT 1"
  assert exc.value.detail.params == ()


def test_fetch_json_raises_structured_error(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def execute(self, q, p):
      raise Exception("boom")
    async def fetchone(self):
      return None

  class Conn:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()
        async def __aexit__(self_inner, exc_type, exc, tb):
          pass
      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  with pytest.raises(db_helpers.DBQueryError) as exc:
    asyncio.run(db_helpers.fetch_json(db_helpers.json_one("SELECT 1")))
  assert exc.value.detail.query == "SELECT 1"


def test_fetch_json_handles_multiple_rows(monkeypatch):
  class Cur:
    def __init__(self):
      self._rows = [("{\"a\":1,\"b\":\"",), ("two\"}",)]
      self._idx = 0
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def execute(self, q, p):
      pass
    async def fetchone(self):
      if self._idx < len(self._rows):
        r = self._rows[self._idx]
        self._idx += 1
        return r
      return None

  class Conn:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()
        async def __aexit__(self_inner, exc_type, exc, tb):
          pass
      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.fetch_json(db_helpers.json_one("SELECT")))
  assert res.rows == [{"a": 1, "b": "two"}]
  assert res.rowcount == 1


def test_exec_query_raises_structured_error(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def execute(self, q, p):
      raise Exception("boom")

  class Conn:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()
        async def __aexit__(self_inner, exc_type, exc, tb):
          pass
      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  with pytest.raises(db_helpers.DBQueryError) as exc:
    asyncio.run(db_helpers.exec_query(db_helpers.exec_op("UPDATE x SET y=1")))
  assert exc.value.detail.query == "UPDATE x SET y=1"


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
    gen = await db_helpers.fetch_rows(db_helpers.row_many("SELECT"), stream=True)
    return hasattr(gen, "__aiter__")

  assert asyncio.run(run())
