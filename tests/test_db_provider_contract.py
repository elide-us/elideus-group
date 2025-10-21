import asyncio
from uuid import UUID

from server.modules.providers.database.mssql_provider import MssqlProvider
import server.modules.providers.database.mssql_provider as mssql_provider
from server.modules.providers import DBResult, DbRunMode
from server.registry.users.files import mssql as users_files_mssql


def test_run_json_one(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:test:json_one:1"
    def handler(args):
      assert args == {}
      return (DbRunMode.JSON_ONE, "select 1", ())
    return handler

  async def fake_fetch_json(sql, params, *, many=False):
    assert sql == "select 1"
    assert params == ()
    assert not many
    return DBResult(rows=[{"v": 1}], rowcount=1)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "fetch_json", fake_fetch_json)

  res = asyncio.run(provider.run("db:test:json_one:1", {}))
  assert isinstance(res, DBResult)
  assert res.rows == [{"v": 1}]
  assert res.rowcount == 1


def test_run_row_one(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:test:row_one:1"
    def handler(args):
      assert args == {}
      return (DbRunMode.ROW_ONE, "select 1", ())
    return handler

  async def fake_fetch_rows(sql, params, *, one=False, stream=False):
    assert sql == "select 1"
    assert params == ()
    assert one
    return DBResult(rows=[{"v": 1}], rowcount=1)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "fetch_rows", fake_fetch_rows)

  res = asyncio.run(provider.run("db:test:row_one:1", {}))
  assert isinstance(res, DBResult)
  assert res.rows == [{"v": 1}]
  assert res.rowcount == 1


def test_run_row_many(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000000"
  async def fake_handler(payload):
    assert payload == {"guid": guid}
    return DBResult(rows=[{"path": "a"}, {"path": "b"}], rowcount=2)

  def fake_get_handler(op):
    assert op == "db:system:public_users:get_published_files:1"
    return fake_handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(
    provider.run("db:system:public_users:get_published_files:1", {"guid": guid})
  )
  assert isinstance(res, DBResult)
  assert res.rows == [{"path": "a"}, {"path": "b"}]
  assert res.rowcount == 2


def test_run_json_many(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:test:json_many:1"
    def handler(args):
      assert args == {}
      return (DbRunMode.JSON_MANY, "select", ())
    return handler

  async def fake_fetch_json(sql, params, *, many=False):
    assert many
    return DBResult(rows=[{"v": 1}, {"v": 2}], rowcount=2)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "fetch_json", fake_fetch_json)

  res = asyncio.run(provider.run("db:test:json_many:1", {}))
  assert isinstance(res, DBResult)
  assert res.rows == [{"v": 1}, {"v": 2}]
  assert res.rowcount == 2


def test_run_exec(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "db:test:exec:1"
    def handler(args):
      assert args == {}
      return (DbRunMode.EXEC, "update", (1,))
    return handler

  async def fake_exec_query(sql, params):
    assert sql == "update"
    assert params == (1,)
    return DBResult(rowcount=1)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "exec_query", fake_exec_query)

  res = asyncio.run(provider.run("db:test:exec:1", {}))
  assert isinstance(res, DBResult)
  assert res.rows == []
  assert res.rowcount == 1


def test_storage_files_set_gallery(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000000"
  expected_guid = str(UUID(guid))

  async def fake_run_exec(sql, params):
    assert "UPDATE users_storage_cache" in sql
    assert params == (1, expected_guid, "", "file.txt")
    return DBResult(rowcount=1)

  monkeypatch.setattr(users_files_mssql, "run_exec", fake_run_exec)

  res = asyncio.run(
    provider.run("db:users:files:set_gallery:1", {"user_guid": guid, "name": "file.txt", "gallery": True})
  )
  assert isinstance(res, DBResult)
  assert res.rowcount == 1
