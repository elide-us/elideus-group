from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  AggregateLineItemsParams,
  DeleteLineItemsByImportParams,
  InsertLineItemsBatchParams,
  ListLineItemsByImportParams,
)

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance staging line items registry")
  return dispatcher


async def insert_line_items_batch_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = InsertLineItemsBatchParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.insert_line_items_batch_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_line_items_by_import_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListLineItemsByImportParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.list_line_items_by_import_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def aggregate_line_items_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = AggregateLineItemsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.aggregate_line_items_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_line_items_by_import_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteLineItemsByImportParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.delete_line_items_by_import_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
