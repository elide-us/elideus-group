"""Content pages query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreatePageParams,
  CreateVersionParams,
  DeletePageParams,
  GetPageBySlugParams,
  GetPageParams,
  GetVersionParams,
  ListPagesParams,
  ListVersionsParams,
  UpdatePageParams,
)

__all__ = [
  "create_v1",
  "create_version_v1",
  "delete_v1",
  "get_by_slug_v1",
  "get_v1",
  "get_version_v1",
  "list_v1",
  "list_versions_v1",
  "update_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_GET_BY_SLUG_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_slug_v1}
_CREATE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_v1}
_UPDATE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_v1}
_CREATE_VERSION_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_version_v1}
_LIST_VERSIONS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_versions_v1}
_GET_VERSION_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_version_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for content pages registry")
  return dispatcher


async def list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListPagesParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetPageParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_by_slug_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetPageBySlugParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_BY_SLUG_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreatePageParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdatePageParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeletePageParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_version_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateVersionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_VERSION_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_versions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListVersionsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_VERSIONS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_version_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetVersionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_VERSION_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
