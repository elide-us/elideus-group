"""Finance status code query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import GetStatusCodeParams, ListStatusCodesParams

__all__ = [
  "get_status_code_v1",
  "list_status_codes_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_status_codes_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_status_code_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance status registry")
  return dispatcher


async def list_status_codes_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListStatusCodesParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_status_code_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetStatusCodeParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
