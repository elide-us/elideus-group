import asyncio
from uuid import uuid4

import pytest

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider import db_helpers
from server.registry.security.accounts import mssql as security_accounts
from server.registry.providers.mssql import PROVIDER_QUERIES
from server.registry.support.users import mssql as support_users
from server.registry.users.profile import mssql as users_profile
from server.registry.security.identities import mssql as security_identities


def _provider_map_for(urn: str) -> str:
  parts = urn.split(":")
  if len(parts) != 5 or parts[0] != "db":
    raise ValueError(f"Unsupported urn: {urn}")
  return f"{parts[1]}.{parts[2]}.{parts[3]}"


def test_mssql_get_by_provider_identifier_uses_user_view():
  op = security_identities.get_by_provider_identifier_v1({
    "provider": "microsoft",
    "provider_identifier": str(uuid4()),
  })
  sql = op.sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql


def test_mssql_get_profile_uses_profile_view():
  op = users_profile.get_profile_v1({"guid": "gid"})
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
def test_mssql_accounts_security_profile_routes_through_security_view(
  args, expected_fragments, joins_users_auth
):
  op = security_accounts.get_security_profile_v1(args)
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
  provider_map = _provider_map_for(urn)
  assert provider_map not in PROVIDER_QUERIES


def test_mssql_support_users_set_credits_updates_table():
  op = support_users.set_credits_v1({"guid": "gid", "credits": 10})
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
  result = asyncio.run(db_helpers.fetch_json(db_helpers.json_many("SELECT 1")))
  assert result.rows == [{"a": 1, "b": "two"}]


def test_execute_operation_handles_exec(monkeypatch):
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
  result = asyncio.run(db_helpers.exec_query(db_helpers.exec_op("UPDATE")))
  assert result.rowcount == 3
