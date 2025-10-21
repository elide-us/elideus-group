import asyncio

from server.registry.users.cache import mssql as cache_mssql
from server.registry.types import DBResponse


def test_storage_cache_upsert_sets_created_on(monkeypatch):
  captured: list[tuple] = []

  async def fake_run_exec(sql, params=()):
    captured.append(tuple(params))
    return DBResponse(rowcount=1)

  async def fake_get_type(mimetype: str, *, allow_folder: bool):
    return 1

  monkeypatch.setattr(cache_mssql, "run_exec", fake_run_exec)
  monkeypatch.setattr(cache_mssql, "_get_storage_type_recid", fake_get_type)

  args = {
    "user_guid": "u",
    "path": "",
    "filename": "file.txt",
    "content_type": "text/plain",
    "public": 0,
    "created_on": None,
    "modified_on": None,
    "url": None,
    "reported": 0,
    "moderation_recid": None,
  }

  asyncio.run(cache_mssql.upsert_v1(args))

  assert captured and captured[0][5] is not None
