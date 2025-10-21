import asyncio
from typing import Any
from uuid import uuid4

import pytest

from server.registry import get_handler
from server.registry.finance.credits import mssql as finance_credits_mssql
from server.registry.types import DBResponse
from server.registry.users.accounts import mssql as accounts_mssql
from server.registry.users.profile import mssql as profile_mssql
from server.registry.users.providers import mssql as users_providers_mssql
from server.modules.providers.database.mssql_provider import db_helpers


def test_users_provider_query_uses_user_view(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(users_providers_mssql, "run_json_one", fake_run_json_one)

  handler = get_handler("db:users:providers:get_by_provider_identifier:1")
  asyncio.run(
    handler({"provider": "microsoft", "provider_identifier": str(uuid4())})
  )
  sql = captured["sql"].lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql


def test_users_profile_get_profile_uses_profile_view(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(profile_mssql, "run_json_one", fake_run_json_one)

  handler = get_handler("db:users:profile:get_profile:1")
  asyncio.run(handler({"guid": "gid"}))
  sql = captured["sql"].lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql
  assert "json_query" in sql
  assert "for json path, without_array_wrapper" in sql


def test_account_security_filters_by_provider(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(accounts_mssql, "run_json_one", fake_run_json_one)

  provider_identifier = str(uuid4())
  handler = get_handler("db:users:account:get_security_profile:1")
  asyncio.run(
    handler({
      "provider": "microsoft",
      "provider_identifier": provider_identifier,
    })
  )
  sql = captured["sql"].lower()
  assert "vw_user_session_security" in sql
  assert "auth_providers" in sql
  assert "ua.element_identifier" in sql
  assert "FOR JSON PATH" in captured["sql"]
  assert captured["params"][0] == "microsoft"
  assert captured["params"][1] == provider_identifier.lower()


def test_account_security_filters_by_discord(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(accounts_mssql, "run_json_one", fake_run_json_one)

  handler = get_handler("db:users:account:get_security_profile:1")
  asyncio.run(handler({"discord_id": "42"}))
  sql = captured["sql"].lower()
  assert "vw_user_session_security" in sql
  assert "auth_providers" in sql
  assert "ua.element_identifier" in sql
  assert any(param == "discord" for param in captured["params"])


def test_finance_credits_set_updates_table(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(finance_credits_mssql, "run_exec", fake_run_exec)
  asyncio.run(finance_credits_mssql.set_credits_v1({"guid": "gid", "credits": 10}))
  assert "update users_credits" in captured["sql"].lower()
  assert captured["params"] == (10, "gid")


def test_fetch_rows_returns_empty_on_error(monkeypatch):
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
  res = asyncio.run(db_helpers.fetch_rows("SELECT 1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_fetch_json_raises_on_error(monkeypatch):
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
        row = self._rows[self._idx]
        self._idx += 1
        return row
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
