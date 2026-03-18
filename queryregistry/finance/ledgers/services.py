"""Finance ledgers query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateLedgerParams,
  DeleteLedgerParams,
  GetLedgerByNameParams,
  GetLedgerParams,
  JournalReferenceCountParams,
  ListLedgersParams,
  UpdateLedgerParams,
)

__all__ = [
  "create_v1",
  "delete_v1",
  "get_by_name_v1",
  "get_v1",
  "journal_reference_count_v1",
  "list_v1",
  "update_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_GET_BY_NAME_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_name_v1}
_CREATE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_v1}
_UPDATE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_v1}
_REFERENCE_COUNT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.journal_reference_count_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance ledgers registry")
  return dispatcher


async def list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListLedgersParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetLedgerParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_by_name_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetLedgerByNameParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_BY_NAME_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateLedgerParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateLedgerParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteLedgerParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def journal_reference_count_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = JournalReferenceCountParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _REFERENCE_COUNT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
