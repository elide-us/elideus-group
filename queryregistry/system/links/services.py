"""System links query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql

__all__ = [
  "get_home_links_v1",
  "get_navbar_routes_v1",
]

_HomeLinksDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_NavbarRoutesDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_HOME_LINKS_DISPATCHERS: dict[str, _HomeLinksDispatcher] = {
  "mssql": mssql.get_home_links,
}

_NAVBAR_ROUTES_DISPATCHERS: dict[str, _NavbarRoutesDispatcher] = {
  "mssql": mssql.get_navbar_routes,
}


async def get_home_links_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _HOME_LINKS_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system links registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def get_navbar_routes_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _NAVBAR_ROUTES_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system links registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)
