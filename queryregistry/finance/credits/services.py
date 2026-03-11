"""Finance credits query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import GetCreditsParams, SetCreditsParams

__all__ = ["get_v1", "set_v1"]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_SET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.set_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance credits registry")
  return dispatcher


async def get_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetCreditsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetCreditsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _SET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
