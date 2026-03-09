"""Reflection data query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import BatchParams, DumpTableParams, UpdateVersionParams, VersionParams

__all__ = [
  "apply_batch_v1",
  "dump_table_v1",
  "get_version_v1",
  "rebuild_indexes_v1",
  "update_version_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_GET_VERSION_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_version_v1}
_UPDATE_VERSION_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_version_v1}
_DUMP_TABLE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.dump_table_v1}
_REBUILD_INDEXES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.rebuild_indexes_v1}
_APPLY_BATCH_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.apply_batch_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for reflection data registry")
  return dispatcher


async def get_version_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = VersionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_VERSION_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_version_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateVersionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_VERSION_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def dump_table_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DumpTableParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DUMP_TABLE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def rebuild_indexes_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _REBUILD_INDEXES_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def apply_batch_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = BatchParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _APPLY_BATCH_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
