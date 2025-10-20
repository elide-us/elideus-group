import asyncio
import importlib.util
import pathlib
import sys
import types
from typing import Any
from uuid import uuid4
import pytest

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


class _BaseProvider:
  def __init__(self, **config):
    self.config = config


class _LifecycleProvider(_BaseProvider):
  async def startup(self):
    return None

  async def shutdown(self):
    return None


class _AuthProviderBase(_LifecycleProvider):
  async def verify_id_token(self, id_token, access_token=None):
    return {}

  async def fetch_user_profile(self, access_token):
    return {}

  def extract_guid(self, payload):
    if isinstance(payload, dict):
      return payload.get("guid")
    return None


class _DbProviderBase(_LifecycleProvider):
  async def run(self, request):
    raise NotImplementedError


class _AuthProvider(_AuthProviderBase):
  def __init__(self, *, audience=None, issuer=None, jwks_uri=None, algorithm="RS256", jwks_expiry=None):
    super().__init__(audience=audience, issuer=issuer, jwks_uri=jwks_uri, algorithm=algorithm, jwks_expiry=jwks_expiry)
    self.audience = audience
    self.issuer = issuer
    self.jwks_uri = jwks_uri
    self.algorithm = algorithm
    self.jwks_expiry = jwks_expiry


providers_pkg.BaseProvider = _BaseProvider
providers_pkg.LifecycleProvider = _LifecycleProvider
providers_pkg.AuthProviderBase = _AuthProviderBase
providers_pkg.DbProviderBase = _DbProviderBase
providers_pkg.AuthProvider = _AuthProvider


class _BaseModule:
  def __init__(self, app=None):
    self.app = app
    self._ready = False

  async def startup(self):
    self._ready = True

  async def shutdown(self):
    self._ready = False

  def mark_ready(self):
    self._ready = True

  async def on_ready(self):
    return self._ready


modules_pkg.BaseModule = _BaseModule
class _DbRunMode:
  ROW_ONE = "row_one"
  ROW_MANY = "row_many"
  JSON_ONE = "json_one"
  JSON_MANY = "json_many"
  EXEC = "exec"


class _DBResult:
  def __init__(self, rows=None, rowcount=0, payload=None):
    if rows is None:
      rows = []
    self.rows = rows
    self.rowcount = rowcount
    self.payload = payload if payload is not None else rows

providers_pkg.DbRunMode = _DbRunMode
providers_pkg.DBResult = _DBResult
sys.modules.setdefault("server.modules.providers", providers_pkg)
database_pkg = types.ModuleType("server.modules.providers.database")
database_pkg.__path__ = [str(root_path / "server/modules/providers/database")]
sys.modules.setdefault("server.modules.providers.database", database_pkg)
mssql_pkg = types.ModuleType("server.modules.providers.database.mssql_provider")
mssql_pkg.__path__ = [str(root_path / "server/modules/providers/database/mssql_provider")]
sys.modules.setdefault("server.modules.providers.database.mssql_provider", mssql_pkg)

registry_pkg = types.ModuleType("server.registry")
registry_pkg.__path__ = [str(root_path / "server/registry")]
sys.modules.setdefault("server.registry", registry_pkg)
registry_types_pkg = types.ModuleType("server.registry.types")
registry_types_pkg.__path__ = [str(root_path / "server/registry")]

class _DBResponse:
  def __init__(self, *, op="", payload=None, rows=None, rowcount=None):
    if rows is not None:
      payload = [dict(row) for row in rows]
      if rowcount is None:
        rowcount = len(payload)
    self.op = op
    self.payload = [] if payload is None else payload
    if rowcount is None:
      rowcount = 0
    self.rowcount = rowcount

  @property
  def rows(self):
    data = self.payload
    if data is None:
      return []
    if isinstance(data, list):
      return data
    if isinstance(data, (tuple, set)):
      return list(data)
    return [data]

class _DBRequest:
  def __init__(self, *, op: str, payload=None, params=None):
    self.op = op
    source = payload if payload is not None else params or {}
    self.payload = dict(source)

  @property
  def params(self):
    return self.payload

registry_types_pkg.DBResponse = _DBResponse
registry_types_pkg.DBRequest = _DBRequest
sys.modules.setdefault("server.registry.types", registry_types_pkg)
registry_pkg.types = registry_types_pkg
providers_pkg.DBRequest = _DBRequest
providers_pkg.DBResponse = _DBResponse
providers_pkg.DBResult = _DBResponse
registry_users_pkg = types.ModuleType("server.registry.users")
registry_users_pkg.__path__ = [str(root_path / "server/registry/users")]
sys.modules.setdefault("server.registry.users", registry_users_pkg)
registry_users_content_pkg = types.ModuleType("server.registry.users.content")
registry_users_content_pkg.__path__ = [str(root_path / "server/registry/users/content")]
sys.modules.setdefault("server.registry.users.content", registry_users_content_pkg)
registry_users_content_profile_pkg = types.ModuleType("server.registry.users.content.profile")
registry_users_content_profile_pkg.__path__ = [str(root_path / "server/registry/users/content/profile")]
sys.modules.setdefault("server.registry.users.content.profile", registry_users_content_profile_pkg)
registry_providers_pkg = types.ModuleType("server.registry.providers")
registry_providers_pkg.__path__ = [str(root_path / "server/registry/providers")]
sys.modules.setdefault("server.registry.providers", registry_providers_pkg)

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

spec_content_profile = importlib.util.spec_from_file_location(
  "server.registry.users.content.profile.mssql",
  root_path / "server/registry/users/content/profile/mssql.py",
)
content_profile_mssql = importlib.util.module_from_spec(spec_content_profile)
sys.modules["server.registry.users.content.profile.mssql"] = content_profile_mssql
spec_content_profile.loader.exec_module(content_profile_mssql)

spec_finance_credits = importlib.util.spec_from_file_location(
  "server.registry.finance.credits.mssql",
  root_path / "server/registry/finance/credits/mssql.py",
)
finance_credits_mssql = importlib.util.module_from_spec(spec_finance_credits)
sys.modules["server.registry.finance.credits.mssql"] = finance_credits_mssql
spec_finance_credits.loader.exec_module(finance_credits_mssql)

def test_mssql_get_by_provider_identifier_uses_user_view():
  handler = get_mssql_handler("db:users:providers:get_by_provider_identifier:1")
  _, sql, _ = handler({"provider": "microsoft", "provider_identifier": str(uuid4())})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_profile_uses_profile_view():
  handler = get_mssql_handler("db:users:profile:get_profile:1")
  _, sql, _ = handler({"guid": "gid"})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql
  assert "json_query" in sql
  assert "for json path, without_array_wrapper" in sql


def test_registry_content_profile_query_uses_json(monkeypatch):
  captured = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    return content_profile_mssql.DBResponse()

  monkeypatch.setattr(content_profile_mssql, "run_json_one", fake_run_json_one)
  asyncio.run(content_profile_mssql.get_profile_v1({"guid": "gid"}))
  sql = captured["sql"].lower()
  assert "json_query" in sql
  assert "for json path, without_array_wrapper" in sql

def test_mssql_get_rotkey_queries_users_and_providers():
  handler = get_mssql_handler("db:users:session:get_rotkey:1")
  _, sql, _ = handler({"guid": "gid"})
  sql = sql.lower()
  assert "from account_users" in sql
  assert "auth_providers" in sql
  assert "vw_account_user_security" not in sql

def test_mssql_get_by_access_token_uses_security_view():
  handler = get_mssql_handler("db:auth:session:get_by_access_token:1")
  _, sql, _ = handler({"access_token": "tok"})
  sql = sql.lower()
  assert "vw_user_session_security" in sql
  assert "user_roles" in sql

def test_mssql_discord_get_security_uses_security_view():
  handler = get_mssql_handler("db:auth:discord:get_security:1")
  _, sql, _ = handler({"discord_id": "42"})
  sql = sql.lower()
  assert "vw_user_session_security" in sql
  assert "auth_providers" in sql


def test_finance_credits_set_updates_table(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return registry_types_pkg.DBResponse()

  monkeypatch.setattr(finance_credits_mssql, "run_exec", fake_run_exec)
  asyncio.run(finance_credits_mssql.set_credits_v1({"guid": "gid", "credits": 10}))
  assert "update users_credits" in captured["sql"].lower()
  assert captured["params"] == (10, "gid")


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


def test_fetch_json_raises_on_error(monkeypatch):
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
  with pytest.raises(Exception):
    asyncio.run(db_helpers.fetch_json("SELECT 1"))


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
  res = asyncio.run(db_helpers.fetch_json("SELECT"))
  assert res.rows == [{"a": 1, "b": "two"}]
  assert res.rowcount == 1


def test_exec_query_raises_on_error(monkeypatch):
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
  with pytest.raises(Exception):
    asyncio.run(db_helpers.exec_query("UPDATE x SET y=1"))


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
