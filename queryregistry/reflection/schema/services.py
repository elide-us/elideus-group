"""Reflection schema query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import ColumnParams, TableParams

__all__ = [
  "get_full_schema_v1",
  "list_columns_v1",
  "list_foreign_keys_v1",
  "list_indexes_v1",
  "list_tables_v1",
  "list_views_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_TABLES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_tables_v1}
_LIST_COLUMNS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_columns_v1}
_LIST_INDEXES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_indexes_v1}
_LIST_FOREIGN_KEYS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_foreign_keys_v1}
_LIST_VIEWS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_views_v1}
_GET_FULL_SCHEMA_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_full_schema_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for reflection schema registry")
  return dispatcher


async def list_tables_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_TABLES_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_columns_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = TableParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_COLUMNS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_indexes_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = TableParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_INDEXES_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_foreign_keys_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = TableParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_FOREIGN_KEYS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_views_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_VIEWS_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_full_schema_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ColumnParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_FULL_SCHEMA_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
