"""System public query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import CmsPathParams, ConfigKeyParams, RoutePathParams, UpsertRouteParams

__all__ = [
  "delete_route_v1",
  "get_cms_tree_for_path_v1",
  "get_config_value_v1",
  "get_home_links_v1",
  "get_navbar_routes_v1",
  "get_routes_v1",
  "list_frontend_pages_v1",
  "upsert_route_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_HOME_LINKS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_home_links}
_NAVBAR_ROUTES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_navbar_routes}
_GET_ROUTES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_routes_v1}
_LIST_FRONTEND_PAGES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_frontend_pages_v1}
_UPSERT_ROUTE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_route_v1}
_DELETE_ROUTE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_route_v1}
_CMS_TREE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_cms_tree_for_path_v1}
_CONFIG_VALUE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_config_value_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system public registry")
  return dispatcher


async def get_home_links_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _HOME_LINKS_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def get_navbar_routes_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _NAVBAR_ROUTES_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def get_routes_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _GET_ROUTES_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_frontend_pages_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_FRONTEND_PAGES_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_route_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertRouteParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_ROUTE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_route_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = RoutePathParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_ROUTE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_cms_tree_for_path_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CmsPathParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CMS_TREE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_config_value_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ConfigKeyParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CONFIG_VALUE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
