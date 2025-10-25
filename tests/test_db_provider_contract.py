import asyncio
from uuid import UUID

from server.modules.providers.database.mssql_provider import MssqlProvider
import server.modules.providers.database.mssql_provider as mssql_provider
from server.modules.providers import DBRequest, DBResponse
from server.registry.account.files import mssql as users_files_mssql


def test_run_returns_dbresult_from_async_handler(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:account:test:json_one:1"

    async def handler(args):
      assert args == {}
      return DBResponse(rows=[{"v": 1}], rowcount=1)

    return handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(
    provider.run(DBRequest(op="db:account:test:json_one:1", payload={}))
  )
  assert isinstance(res, DBResponse)
  assert res.rows == [{"v": 1}]
  assert res.rowcount == 1


def test_run_returns_dbresult_from_sync_handler(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:account:test:row_one:1"

    def handler(args):
      assert args == {}
      return DBResponse(rows=[{"v": 1}], rowcount=1)

    return handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(
    provider.run(DBRequest(op="db:account:test:row_one:1", payload={}))
  )
  assert isinstance(res, DBResponse)
  assert res.rows == [{"v": 1}]
  assert res.rowcount == 1


def test_run_row_many(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000000"

  async def fake_handler(payload):
    assert payload == {"guid": guid}
    return DBResponse(rows=[{"path": "a"}, {"path": "b"}], rowcount=2)

  def fake_get_handler(op):
    assert op == "db:system:public_users:get_published_files:1"
    return fake_handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(
    provider.run(
      DBRequest(
        op="db:system:public_users:get_published_files:1",
        payload={"guid": guid},
      )
    )
  )
  assert isinstance(res, DBResponse)
  assert res.rows == [{"path": "a"}, {"path": "b"}]
  assert res.rowcount == 2


def test_run_normalizes_dict_response(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:account:test:json_many:1"

    def handler(args):
      assert args == {}
      return {"rows": [{"v": 1}, {"v": 2}], "rowcount": 2}

    return handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(
    provider.run(DBRequest(op="db:account:test:json_many:1", payload={}))
  )
  assert isinstance(res, DBResponse)
  assert res.rows == [{"v": 1}, {"v": 2}]
  assert res.rowcount == 2


def test_run_returns_empty_response_for_none(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:account:test:exec:1"

    def handler(args):
      assert args == {}
      return None

    return handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(
    provider.run(DBRequest(op="db:account:test:exec:1", payload={}))
  )
  assert isinstance(res, DBResponse)
  assert res.rows == []
  assert res.rowcount == 0


def test_storage_files_set_gallery(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000000"
  expected_guid = str(UUID(guid))

  async def fake_run_exec(sql, params):
    assert "UPDATE users_storage_cache" in sql
    assert params == (1, expected_guid, "", "file.txt")
    return DBResponse(rowcount=1)

  monkeypatch.setattr(users_files_mssql, "run_exec", fake_run_exec)

  res = asyncio.run(
    provider.run(
      DBRequest(
        op="db:account:files:set_gallery:1",
        payload={"user_guid": guid, "name": "file.txt", "gallery": True},
      )
    )
  )
  assert isinstance(res, DBResponse)
  assert res.rowcount == 1
