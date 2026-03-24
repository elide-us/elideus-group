"""System renewals query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  DeleteRenewalParams,
  GetRenewalParams,
  ListRenewalsParams,
  UpsertRenewalParams,
)

__all__ = [
  "delete_renewal_v1",
  "get_renewal_v1",
  "list_renewals_v1",
  "upsert_renewal_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_renewals_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_renewal_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_renewal_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_renewal_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system renewals registry")
  return dispatcher


async def list_renewals_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListRenewalsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_renewal_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetRenewalParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_renewal_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertRenewalParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_renewal_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteRenewalParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
