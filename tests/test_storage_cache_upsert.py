import asyncio

from server.registry.content.cache import mssql as content_cache
from server.registry.types import DBResponse


def test_storage_cache_upsert_sets_created_on(monkeypatch):
  captured = []

  async def fake_run_exec(sql, params, *, timeout=None, meta=None):
    captured.append(params)
    return DBResponse(rowcount=1)

  async def fake_get_storage_type_recid(*_args, **_kwargs):
    return 1

  monkeypatch.setattr(content_cache, "run_exec", fake_run_exec)
  monkeypatch.setattr(content_cache, "_get_storage_type_recid", fake_get_storage_type_recid)

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

  asyncio.run(content_cache.upsert_v1(args))

  assert captured and captured[0][5] is not None
