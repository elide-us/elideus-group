"""Content indexing query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CacheItemKey,
  DeleteCacheFolderParams,
  GetPublishedFilesParams,
  ListCacheParams,
  ReplaceUserCacheParams,
  SetGalleryParams,
  SetPublicParams,
  SetReportedParams,
  UpsertCacheItemParams,
)

__all__ = [
  "count_rows_v1",
  "delete_folder_v1",
  "delete_v1",
  "get_published_files_v1",
  "list_public_v1",
  "list_reported_v1",
  "list_v1",
  "replace_user_v1",
  "set_gallery_v1",
  "set_public_v1",
  "set_reported_v1",
  "upsert_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_LIST_PUBLIC_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_public_v1}
_LIST_REPORTED_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_reported_v1}
_REPLACE_USER_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.replace_user_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_v1}
_DELETE_FOLDER_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_folder_v1}
_SET_PUBLIC_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.set_public_v1}
_SET_REPORTED_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.set_reported_v1}
_COUNT_ROWS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.count_rows_v1}
_SET_GALLERY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.set_gallery_v1}
_GET_PUBLISHED_FILES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_published_files_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for content indexing registry")
  return dispatcher


async def list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListCacheParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_public_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_PUBLIC_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_reported_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_REPORTED_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def replace_user_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ReplaceUserCacheParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _REPLACE_USER_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertCacheItemParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CacheItemKey.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_folder_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteCacheFolderParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_FOLDER_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_public_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetPublicParams.model_validate(request.payload)
  payload = params.model_dump(exclude_none=True)
  payload["public"] = 1 if params.public else 0
  result = await _select_dispatcher(provider, _SET_PUBLIC_DISPATCHERS)(payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_reported_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetReportedParams.model_validate(request.payload)
  payload = params.model_dump()
  payload["reported"] = 1 if params.reported else 0
  result = await _select_dispatcher(provider, _SET_REPORTED_DISPATCHERS)(payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def count_rows_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _COUNT_ROWS_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_gallery_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetGalleryParams.model_validate(request.payload)
  payload = params.model_dump(exclude_none=True)
  payload["gallery"] = 1 if params.gallery else 0
  result = await _select_dispatcher(provider, _SET_GALLERY_DISPATCHERS)(payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_published_files_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetPublishedFilesParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_PUBLISHED_FILES_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
