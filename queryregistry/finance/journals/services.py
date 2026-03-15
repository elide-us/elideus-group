"""Finance journals query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateJournalParams,
  GetByPostingKeyParams,
  GetJournalParams,
  ListJournalsParams,
  UpdateJournalStatusParams,
)

__all__ = ["create_v1", "get_by_posting_key_v1", "get_v1", "list_v1", "update_status_v1"]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_CREATE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_v1}
_UPDATE_STATUS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_status_v1}
_GET_BY_POSTING_KEY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_posting_key_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance journals registry")
  return dispatcher


async def list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListJournalsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetJournalParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateJournalParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_status_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateJournalStatusParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_STATUS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_by_posting_key_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetByPostingKeyParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_BY_POSTING_KEY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
