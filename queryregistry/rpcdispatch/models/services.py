"""RPC dispatch models query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import ListModelsParams, GetModelParams, GetByNameParams, UpsertModelParams, DeleteModelParams

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_models_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_model_v1}
_GETBYNAME_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_name_models_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_model_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_model_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for rpcdispatch models registry")
  return dispatcher

async def list_models_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListModelsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def get_models_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetModelParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def get_by_name_models_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetByNameParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GETBYNAME_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def upsert_models_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertModelParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def delete_models_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteModelParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

