"""RPC dispatch model_fields query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import ListModelFieldsParams, GetModelFieldParams, ListByModelParams, UpsertModelFieldParams, DeleteModelFieldParams

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_model_fields_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_model_field_v1}
_LISTBYMODEL_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_model_model_fields_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_model_field_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_model_field_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for rpcdispatch model_fields registry")
  return dispatcher

async def list_model_fields_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListModelFieldsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def get_model_fields_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetModelFieldParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def list_by_model_model_fields_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListByModelParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LISTBYMODEL_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def upsert_model_fields_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertModelFieldParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def delete_model_fields_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteModelFieldParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

