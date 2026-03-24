"""RPC dispatch functions query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import ListFunctionsParams, GetFunctionParams, ListBySubdomainParams, UpsertFunctionParams, DeleteFunctionParams

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_functions_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_function_v1}
_LISTBYSUBDOMAIN_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_subdomain_functions_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_function_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_function_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for rpcdispatch functions registry")
  return dispatcher

async def list_functions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListFunctionsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def get_functions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetFunctionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def list_by_subdomain_functions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListBySubdomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LISTBYSUBDOMAIN_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def upsert_functions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertFunctionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def delete_functions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteFunctionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

