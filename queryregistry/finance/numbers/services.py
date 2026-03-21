"""Finance numbers query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CloseSequenceParams,
  DeleteNumberParams,
  GetByScopeParams,
  GetByPrefixAndAccountNumberParams,
  GetNumberParams,
  ListNumbersParams,
  NextNumberByScopeParams,
  NextNumberParams,
  UpsertNumberParams,
)

__all__ = [
  "close_sequence_v1",
  "delete_v1",
  "get_by_prefix_account_v1",
  "get_by_scope_v1",
  "get_v1",
  "list_v1",
  "next_number_by_scope_v1",
  "next_number_v1",
  "upsert_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_GET_BY_PREFIX_ACCOUNT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_prefix_and_account_v1}
_GET_BY_SCOPE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_scope_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_v1}
_CLOSE_SEQUENCE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.close_sequence_v1}
_NEXT_NUMBER_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.next_number_v1}
_NEXT_NUMBER_BY_SCOPE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.next_number_by_scope_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance numbers registry")
  return dispatcher


async def list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListNumbersParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)




async def get_by_prefix_account_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetByPrefixAndAccountNumberParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_BY_PREFIX_ACCOUNT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_by_scope_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetByScopeParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_BY_SCOPE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetNumberParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertNumberParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteNumberParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def close_sequence_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CloseSequenceParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CLOSE_SEQUENCE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def next_number_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = NextNumberParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _NEXT_NUMBER_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def next_number_by_scope_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = NextNumberByScopeParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _NEXT_NUMBER_BY_SCOPE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
