import asyncio
import asyncio
from typing import Any
from uuid import uuid4

import pytest

from server.modules.providers.database.mssql_provider import db_helpers
from server.modules.providers import DbRunMode
from server.registry.users.security.accounts import mssql as security_accounts
from server.registry.providers.mssql import PROVIDER_QUERIES
from server.registry.users.security.identities import mssql as security_identities
import server.registry.finance.credits.mssql as finance_credits_backend
from server.registry.finance.credits import set_credits_request
import server.registry.users.content.profile.mssql as users_profile_backend
from server.registry.types import DBResponse


def _provider_map_for(urn: str) -> str:
  parts = urn.split(":")
  if len(parts) != 5 or parts[0] != "db":
    raise ValueError(f"Unsupported urn: {urn}")
  return f"{parts[1]}.{parts[2]}.{parts[3]}"


def test_mssql_get_by_provider_identifier_uses_user_view(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params=(), *, meta=None):
    captured["sql"] = sql
    captured["params"] = params
    return DBResponse()

  monkeypatch.setattr(security_identities, "run_json_one", fake_run_json_one)
  asyncio.run(security_identities.get_by_provider_identifier_v1({
    "provider": "microsoft",
    "provider_identifier": str(uuid4()),
  }))
  sql = captured["sql"].lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql


def test_mssql_get_profile_uses_profile_view(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params=(), *, meta=None):
    captured["sql"] = sql
    captured["params"] = params
    return DBResponse()

  monkeypatch.setattr(users_profile_backend, "run_json_one", fake_run_json_one)
  asyncio.run(users_profile_backend.get_profile_v1({"guid": "gid"}))
  sql = captured["sql"].lower()
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
def test_mssql_accounts_security_profile_routes_through_security_view(
  monkeypatch,
  args,
  expected_fragments,
  joins_users_auth,
):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params=(), *, meta=None):
    captured["sql"] = sql
    captured["params"] = params
    return DBResponse()

  monkeypatch.setattr(security_accounts, "run_json_one", fake_run_json_one)
  asyncio.run(security_accounts.get_security_profile_v1(args))
  sql = captured["sql"].lower()
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
  provider_map = _provider_map_for(urn)
  assert provider_map not in PROVIDER_QUERIES


def test_mssql_finance_credits_set_credits_updates_table(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params, *, meta=None):
    captured["sql"] = sql
    captured["params"] = params
    return DBResponse()

  monkeypatch.setattr(finance_credits_backend, "run_exec", fake_run_exec)
  asyncio.run(finance_credits_backend.set_credits_v1({"guid": "gid", "credits": 10}))
  assert "update users_credits" in captured["sql"].lower()
  assert captured["params"] == (10, "gid")


def test_users_credits_route_registered():
  request = set_credits_request(guid="gid", credits=10)
  provider_map = _provider_map_for(request.op)
  assert provider_map in PROVIDER_QUERIES


def test_account_users_route_removed():
  provider_map = _provider_map_for("db:account:users:set_credits:1")
  assert provider_map not in PROVIDER_QUERIES


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
    asyncio.run(db_helpers.fetch_rows(DbRunMode.ROW_ONE, "SELECT 1"))
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
    asyncio.run(db_helpers.fetch_json(DbRunMode.JSON_ONE, "SELECT 1"))
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
      if self._idx >= len(self._rows):
        return None
      row = self._rows[self._idx]
      self._idx += 1
      return row

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
  result = asyncio.run(db_helpers.fetch_json(DbRunMode.JSON_MANY, "SELECT 1"))
  assert result.rows == [{"a": 1, "b": "two"}]


def test_run_operation_handles_exec(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def execute(self, q, p):
      pass
    @property
    def rowcount(self):
      return 3

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
  result = asyncio.run(db_helpers.run_operation(DbRunMode.EXEC, "UPDATE"))
  assert result.rowcount == 3
