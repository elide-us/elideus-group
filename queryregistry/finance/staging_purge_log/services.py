from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CheckPurgedKeyParams,
  GetPurgeLogParams,
  ListPurgeLogsParams,
  UpsertPurgeLogParams,
)

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance staging purge log registry")
  return dispatcher


async def list_purge_logs_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListPurgeLogsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.list_purge_logs_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_purge_log_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetPurgeLogParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.get_purge_log_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def check_purged_key_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CheckPurgedKeyParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.check_purged_key_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_purge_log_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertPurgeLogParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.upsert_purge_log_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def append_purged_keys(db, vendors_recid: int, period_key: str, new_keys: list[str]) -> None:
  existing_res = await db.run(
    DBRequest(
      op="db:finance:staging_purge_log:get_purge_log:1",
      payload={"vendors_recid": vendors_recid, "period_key": period_key},
    )
  )
  existing_keys: set[str] = set()
  if existing_res.rows:
    row = existing_res.rows[0] if isinstance(existing_res.rows, list) else existing_res.rows
    raw = row.get("element_purged_keys") or '{"batch_purged": []}'
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    existing_keys = set(parsed.get("batch_purged", []))

  merged = existing_keys | set(new_keys)
  merged_json = json.dumps({"batch_purged": sorted(merged)})

  await db.run(
    DBRequest(
      op="db:finance:staging_purge_log:upsert_purge_log:1",
      payload={
        "vendors_recid": vendors_recid,
        "period_key": period_key,
        "purged_keys_json": merged_json,
        "purged_count": len(merged),
      },
    )
  )
