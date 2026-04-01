"""Reflection EDT query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql

__all__ = ["list_edt_v1"]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_edt_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for reflection edt registry")
  return dispatcher


async def list_edt_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
