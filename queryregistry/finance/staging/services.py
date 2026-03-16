"""Finance staging query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateImportParams,
  DeleteImportParams,
  InsertCostDetailBatchParams,
  ListCostDetailsByImportParams,
  ListImportsParams,
  UpdateImportStatusParams,
)

__all__ = [
  "create_import_v1",
  "delete_import_v1",
  "insert_cost_detail_batch_v1",
  "list_cost_details_by_import_v1",
  "list_imports_v1",
  "update_import_status_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_CREATE_IMPORT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_import_v1}
_DELETE_IMPORT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_import_v1}
_UPDATE_IMPORT_STATUS_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.update_import_status_v1,
}
_INSERT_COST_DETAIL_BATCH_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.insert_cost_detail_batch_v1,
}
_LIST_IMPORTS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_imports_v1}
_LIST_COST_DETAILS_BY_IMPORT_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.list_cost_details_by_import_v1,
}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance staging registry")
  return dispatcher


async def create_import_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateImportParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_IMPORT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_import_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteImportParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_IMPORT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_import_status_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateImportStatusParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_IMPORT_STATUS_DISPATCHERS)(
    params.model_dump(),
  )
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def insert_cost_detail_batch_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = InsertCostDetailBatchParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _INSERT_COST_DETAIL_BATCH_DISPATCHERS)(
    params.model_dump(),
  )
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_imports_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListImportsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_IMPORTS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_cost_details_by_import_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListCostDetailsByImportParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_COST_DETAILS_BY_IMPORT_DISPATCHERS)(
    params.model_dump(),
  )
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
