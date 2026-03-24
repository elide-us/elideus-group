"""Finance product journal config query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  ActivateProductJournalConfigParams,
  ApproveProductJournalConfigParams,
  CloseProductJournalConfigParams,
  GetActiveConfigParams,
  GetProductJournalConfigParams,
  ListProductJournalConfigParams,
  UpsertProductJournalConfigParams,
)

__all__ = ["activate_v1", "approve_v1", "close_v1", "get_active_v1", "get_v1", "list_v1", "upsert_v1"]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_GET_ACTIVE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_active_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_v1}
_APPROVE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.approve_v1}
_ACTIVATE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.activate_v1}
_CLOSE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.close_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance product_journal_config registry")
  return dispatcher


async def list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListProductJournalConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetProductJournalConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_active_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetActiveConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_ACTIVE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertProductJournalConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def approve_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ApproveProductJournalConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _APPROVE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def activate_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ActivateProductJournalConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _ACTIVATE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def close_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CloseProductJournalConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CLOSE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
