"""MSSQL provider callable bindings."""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from typing import Any

from server.modules.providers import DBResult
from server.modules.providers.database.mssql_provider.db_helpers import Operation, execute_operation
from server.registry.content.cache import mssql as content_cache
from server.registry.content.files import mssql as content_files
from server.registry.content.public import mssql as content_public
from server.registry.types import DBRequest, DBResponse

from . import ProviderCallable, ProviderQueryMap

__all__ = [
  "PROVIDER_QUERIES",
]


async def _coerce_response(spec: Any) -> DBResponse:
  if isinstance(spec, DBResponse):
    return spec
  if inspect.isawaitable(spec):
    return await _coerce_response(await spec)
  if isinstance(spec, Operation):
    result = await execute_operation(spec)
    return DBResponse.from_result(result)
  if isinstance(spec, DBResult):
    return DBResponse.from_result(spec)
  if isinstance(spec, Mapping):
    validator = getattr(DBResult, "model_validate", None)
    if callable(validator):
      return DBResponse.from_result(validator(spec))
    return DBResponse.from_result(DBResult(**spec))
  if spec is None:
    return DBResponse()
  raise TypeError(f"Unsupported provider specification result: {type(spec)!r}")


def _wrap(fn: Any) -> ProviderCallable:
  async def _executor(request: DBRequest) -> DBResponse:
    spec = fn(request.params)
    return await _coerce_response(spec)
  return _executor


PROVIDER_QUERIES: ProviderQueryMap = {
  "content.cache.list": {
    1: _wrap(content_cache.list_v1),
  },
  "content.cache.replace_user": {
    1: _wrap(content_cache.replace_user_v1),
  },
  "content.cache.upsert": {
    1: _wrap(content_cache.upsert_v1),
  },
  "content.cache.delete": {
    1: _wrap(content_cache.delete_v1),
  },
  "content.cache.delete_folder": {
    1: _wrap(content_cache.delete_folder_v1),
  },
  "content.cache.set_public": {
    1: _wrap(content_cache.set_public_v1),
  },
  "content.cache.set_reported": {
    1: _wrap(content_cache.set_reported_v1),
  },
  "content.cache.count_rows": {
    1: _wrap(content_cache.count_rows_v1),
  },
  "content.public.list_public": {
    1: _wrap(content_public.list_public_v1),
  },
  "content.public.list_reported": {
    1: _wrap(content_public.list_reported_v1),
  },
  "content.public.get_public_files": {
    1: _wrap(content_public.get_public_files_v1),
  },
  "content.files.set_gallery": {
    1: _wrap(content_files.set_gallery_v1),
  },
}
