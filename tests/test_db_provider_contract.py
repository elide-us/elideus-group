import asyncio
from uuid import UUID

from server.modules.providers.database.mssql_provider import MssqlProvider
from server.modules.providers import DBRequest, DBResponse
from server.registry.account.files import mssql as users_files_mssql


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
