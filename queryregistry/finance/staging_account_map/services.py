"""Finance staging account map query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  DeleteAccountMapParams,
  GetAccountMapParams,
  ListAccountMapParams,
  ResolveAccountParams,
  UpsertAccountMapParams,
)

__all__ = [
  "delete_account_map_v1",
  "get_account_map_v1",
  "list_account_map_v1",
  "resolve_account_v1",
  "upsert_account_map_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_account_map_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_account_map_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_account_map_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_account_map_v1}
_RESOLVE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.resolve_account_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance staging account map registry")
  return dispatcher


async def list_account_map_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListAccountMapParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_account_map_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetAccountMapParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_account_map_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertAccountMapParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_account_map_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteAccountMapParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def resolve_account_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ResolveAccountParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _RESOLVE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
