import asyncio
from uuid import UUID

from server.modules.providers.database.mssql_provider import MssqlProvider
import server.modules.providers.database.mssql_provider as mssql_provider
from server.modules.providers import DBResult, DbRunMode


def test_run_json_one(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "test:json_one"
    def handler(args):
      assert args == {}
      return mssql_provider.Operation(DbRunMode.JSON_ONE, "select 1", ())
    return handler

  async def fake_execute_operation(operation):
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.JSON_ONE
    assert operation.sql == "select 1"
    assert operation.params == ()
    return DBResult(rows=[{"v": 1}], rowcount=1)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  res = asyncio.run(provider.run("test:json_one", {}))
  assert isinstance(res, DBResult)
  assert res.rows == [{"v": 1}]
  assert res.rowcount == 1


def test_run_row_one(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "test:row_one"
    def handler(args):
      assert args == {}
      return mssql_provider.Operation(DbRunMode.ROW_ONE, "select 1", ())
    return handler

  async def fake_execute_operation(operation):
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.ROW_ONE
    assert operation.sql == "select 1"
    assert operation.params == ()
    return DBResult(rows=[{"v": 1}], rowcount=1)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  res = asyncio.run(provider.run("test:row_one", {}))
  assert isinstance(res, DBResult)
  assert res.rows == [{"v": 1}]
  assert res.rowcount == 1


def test_run_row_many(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000000"
  expected_guid = str(UUID(guid))

  async def fake_execute_operation(operation):
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.JSON_MANY
    assert "FOR JSON PATH" in operation.sql
    assert operation.params == (expected_guid,)
    return DBResult(rows=[{"path": "a"}, {"path": "b"}], rowcount=2)

  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  res = asyncio.run(provider.run("db:public:users:get_published_files:1", {"guid": guid}))
  assert isinstance(res, DBResult)
  assert res.rows == [{"path": "a"}, {"path": "b"}]
  assert res.rowcount == 2


def test_run_json_many(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "test:json_many"
    def handler(args):
      assert args == {}
      return mssql_provider.Operation(DbRunMode.JSON_MANY, "select", ())
    return handler

  async def fake_execute_operation(operation):
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.JSON_MANY
    return DBResult(rows=[{"v": 1}, {"v": 2}], rowcount=2)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  res = asyncio.run(provider.run("test:json_many", {}))
  assert isinstance(res, DBResult)
  assert res.rows == [{"v": 1}, {"v": 2}]
  assert res.rowcount == 2


def test_run_exec(monkeypatch):
  provider = MssqlProvider()

  def fake_get_handler(op):
    assert op == "test:exec"
    def handler(args):
      assert args == {}
      return mssql_provider.Operation(DbRunMode.EXEC, "update", (1,))
    return handler

  async def fake_execute_operation(operation):
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.EXEC
    assert operation.sql == "update"
    assert operation.params == (1,)
    return DBResult(rowcount=1)

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)
  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  res = asyncio.run(provider.run("test:exec", {}))
  assert isinstance(res, DBResult)
  assert res.rows == []
  assert res.rowcount == 1


def test_storage_files_set_gallery(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000000"
  expected_guid = str(UUID(guid))

  async def fake_execute_operation(operation):
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.EXEC
    assert "UPDATE users_storage_cache" in operation.sql
    assert operation.params == (1, expected_guid, "", "file.txt")
    return DBResult(rowcount=1)

  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  res = asyncio.run(provider.run("db:content:files:set_gallery:1", {"user_guid": guid, "name": "file.txt", "gallery": True}))
  assert isinstance(res, DBResult)
  assert res.rowcount == 1


def test_storage_cache_set_public(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000001"
  expected_guid = str(UUID(guid))

  async def fake_execute_operation(operation):
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.EXEC
    assert operation.params == (0, expected_guid, "docs", "file.txt")
    assert "UPDATE users_storage_cache" in operation.sql
    return DBResult(rowcount=1)

  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  res = asyncio.run(provider.run("db:content:cache:set_public:1", {
    "user_guid": guid,
    "path": "docs",
    "filename": "file.txt",
    "public": False,
  }))
  assert isinstance(res, DBResult)
  assert res.rowcount == 1


def test_storage_public_lists_share_query(monkeypatch):
  provider = MssqlProvider()
  seen = []

  async def fake_execute_operation(operation):
    seen.append(operation)
    assert isinstance(operation, mssql_provider.Operation)
    assert operation.kind is DbRunMode.JSON_MANY
    assert operation.params == ()
    return DBResult(rows=[], rowcount=0)

  monkeypatch.setattr(mssql_provider, "execute_operation", fake_execute_operation)

  asyncio.run(provider.run("db:content:public:list_public:1", {}))
  asyncio.run(provider.run("db:content:public:get_public_files:1", {}))

  assert len(seen) == 2
  assert seen[0].sql == seen[1].sql


def test_unlink_provider_dict_result(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000002"

  def fake_get_handler(op):
    assert op == "db:security:identities:unlink_provider:1"

    async def handler(args):
      assert args == {
        "guid": guid,
        "provider": "google",
        "new_provider_recid": 123,
      }
      return {"rows": [{"providers_remaining": 1}], "rowcount": 1}

    return handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(provider.run("db:security:identities:unlink_provider:1", {
    "guid": guid,
    "provider": "google",
    "new_provider_recid": 123,
  }))

  assert isinstance(res, DBResult)
  assert res.rows == [{"providers_remaining": 1}]
  assert res.rowcount == 1


def test_create_session_dict_result(monkeypatch):
  provider = MssqlProvider()
  guid = "00000000-0000-0000-0000-000000000003"

  def fake_get_handler(op):
    assert op == "db:security:sessions:create_session:1"

    async def handler(args):
      assert args == {
        "access_token": "token",
        "expires": "2024-01-01T00:00:00Z",
        "fingerprint": "fingerprint",
        "user_agent": "pytest",
        "ip_address": "127.0.0.1",
        "user_guid": guid,
        "provider": "google",
      }
      return {
        "rows": [{"session_guid": "sess", "device_guid": "device"}],
        "rowcount": 1,
      }

    return handler

  monkeypatch.setattr(mssql_provider, "get_handler", fake_get_handler)

  res = asyncio.run(provider.run("db:security:sessions:create_session:1", {
    "access_token": "token",
    "expires": "2024-01-01T00:00:00Z",
    "fingerprint": "fingerprint",
    "user_agent": "pytest",
    "ip_address": "127.0.0.1",
    "user_guid": guid,
    "provider": "google",
  }))

  assert isinstance(res, DBResult)
  assert res.rows == [{"session_guid": "sess", "device_guid": "device"}]
  assert res.rowcount == 1
