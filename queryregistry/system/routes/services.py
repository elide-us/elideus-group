"""System routes query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import RoutePathParams, UpsertRouteParams

__all__ = [
  "delete_route_v1",
  "get_routes_v1",
  "upsert_route_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_GET_ROUTES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_routes_v1}
_UPSERT_ROUTE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_route_v1}
_DELETE_ROUTE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_route_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system routes registry")
  return dispatcher


async def get_routes_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _GET_ROUTES_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_route_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertRouteParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_ROUTE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_route_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = RoutePathParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_ROUTE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
