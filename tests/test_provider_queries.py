import asyncio
from typing import Any
from uuid import uuid4

import pytest

from server.registry import get_handler
from server.registry.finance.credits import mssql as finance_credits_mssql
from server.registry.types import DBResponse
from server.registry.account.actions import mssql as actions_mssql
from server.registry.account.accounts import mssql as accounts_mssql
from server.registry.account.enablements import mssql as enablements_mssql
from server.registry.account.profile import mssql as profile_mssql
from server.registry.account.providers import mssql as users_providers_mssql
from server.registry.account.session import mssql as session_mssql
from server.registry.system.service_pages import mssql as service_pages_mssql
from server.modules.providers.database.mssql_provider import db_helpers


def test_users_provider_query_uses_user_view(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(users_providers_mssql, "run_json_one", fake_run_json_one)

  handler = get_handler("db:account:providers:get_by_provider_identifier:1")
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

  handler = get_handler("db:account:profile:get_profile:1")
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
  handler = get_handler("db:account:accounts:get_security_profile:1")
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

  handler = get_handler("db:account:accounts:get_security_profile:1")
  asyncio.run(handler({"discord_id": "42"}))
  sql = captured["sql"].lower()
  assert "vw_user_session_security" in sql
  assert "auth_providers" in sql
  assert "ua.element_identifier" in sql
  assert any(param == "discord" for param in captured["params"])


def test_account_enablements_get_by_user_uses_table(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(enablements_mssql, "run_json_one", fake_run_json_one)

  guid = str(uuid4())
  handler = get_handler("db:account:enablements:get_by_user:1")
  asyncio.run(handler({"users_guid": guid}))
  sql = captured["sql"].lower()
  assert "from users_enablements" in sql
  assert "for json path" in sql
  assert captured["params"] == (guid,)


def test_account_enablements_upsert_inserts_when_missing(monkeypatch):
  calls: list[tuple[str, tuple[Any, ...]]] = []

  async def fake_run_exec(sql, params):
    calls.append((sql, tuple(params)))
    if "update users_enablements" in sql.lower():
      return DBResponse(rowcount=0)
    return DBResponse(rowcount=1)

  monkeypatch.setattr(enablements_mssql, "run_exec", fake_run_exec)

  guid = str(uuid4())
  asyncio.run(
    enablements_mssql.upsert_v1({
      "users_guid": guid,
      "element_enablements": "111",
    })
  )

  sql_calls = [sql.lower() for sql, _ in calls]
  assert any("update users_enablements" in sql for sql in sql_calls)
  assert any("insert into users_enablements" in sql for sql in sql_calls)


def test_account_actions_list_by_user_joins_actions(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_many(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(actions_mssql, "run_json_many", fake_run_json_many)

  guid = str(uuid4())
  handler = get_handler("db:account:actions:list_by_user:1")
  asyncio.run(handler({"users_guid": guid, "limit": 5}))
  sql = captured["sql"].lower()
  assert "from users_actions_log" in sql
  assert "left join account_actions" in sql
  assert "fetch next ? rows only" in sql
  assert captured["params"][-1] == 5


def test_account_actions_log_inserts_log_table(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(actions_mssql, "run_exec", fake_run_exec)

  guid = str(uuid4())
  asyncio.run(
    actions_mssql.log_v1({
      "recid": 100,
      "users_guid": guid,
      "action_recid": 42,
    })
  )

  sql = captured["sql"].lower()
  assert "insert into users_actions_log" in sql
  assert captured["params"][:3] == (100, guid, 42)


def test_account_actions_update_builds_dynamic_assignments(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(actions_mssql, "run_exec", fake_run_exec)

  asyncio.run(
    actions_mssql.update_v1({
      "recid": 10,
      "element_url": "https://example", 
      "element_notes": "note",
    })
  )

  sql = captured["sql"].lower()
  assert "update users_actions_log" in sql
  assert "element_url = ?" in sql
  assert "element_notes = ?" in sql
  assert captured["params"][-1] == 10


def test_account_session_list_snapshots_uses_view(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_many(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(session_mssql, "run_json_many", fake_run_json_many)

  guid = str(uuid4())
  handler = get_handler("db:account:session:list_snapshots:1")
  asyncio.run(handler({"guid": guid}))
  sql = captured["sql"].lower()
  assert "vw_user_session_security" in sql
  assert "for json path" in sql


def test_account_session_security_snapshot_uses_view(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_many(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(session_mssql, "run_json_many", fake_run_json_many)

  guid = str(uuid4())
  handler = get_handler("db:account:session:get_security_snapshot:1")
  asyncio.run(handler({"guid": guid}))
  sql = captured["sql"].lower()
  assert "vw_user_session_security" in sql
  assert "order by" in sql


def test_service_pages_list_filters_active(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_many(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(service_pages_mssql, "run_json_many", fake_run_json_many)

  handler = get_handler("db:system:service_pages:list:1")
  asyncio.run(handler({"element_is_active": True}))
  sql = captured["sql"].lower()
  assert "from service_pages" in sql
  assert "element_is_active = ?" in sql
  assert captured["params"] == (1,)


def test_service_pages_create_inserts_table(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(service_pages_mssql, "run_exec", fake_run_exec)

  guid = str(uuid4())
  asyncio.run(
    service_pages_mssql.create_v1({
      "recid": 5,
      "element_route_name": "home",
      "element_pageblob": "<p>hi</p>",
      "element_version": 3,
      "element_created_by": guid,
      "element_modified_by": guid,
      "element_is_active": False,
    })
  )

  sql = captured["sql"].lower()
  assert "insert into service_pages" in sql
  assert captured["params"][0] == 5
  assert captured["params"][-1] == 0


def test_service_pages_update_sets_modified_fields(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(service_pages_mssql, "run_exec", fake_run_exec)

  guid = str(uuid4())
  asyncio.run(
    service_pages_mssql.update_v1({
      "recid": 8,
      "element_modified_by": guid,
      "element_pageblob": "<p>updated</p>",
      "element_is_active": True,
    })
  )

  sql = captured["sql"].lower()
  assert "update service_pages" in sql
  assert "element_modified_on = sysutcdatetime()" in sql
  assert captured["params"][0] == guid
  assert captured["params"][-1] == 8


def test_service_pages_delete_uses_table(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_exec(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse()

  monkeypatch.setattr(service_pages_mssql, "run_exec", fake_run_exec)

  asyncio.run(service_pages_mssql.delete_v1({"recid": 12}))
  sql = captured["sql"].lower()
  assert "delete from service_pages" in sql
  assert captured["params"] == (12,)


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
