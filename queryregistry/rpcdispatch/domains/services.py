"""RPC dispatch domains query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import ListDomainsParams, GetDomainParams, GetByNameParams, UpsertDomainParams, DeleteDomainParams

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_domains_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_domain_v1}
_GETBYNAME_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_name_domains_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_domain_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_domain_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for rpcdispatch domains registry")
  return dispatcher

async def list_domains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListDomainsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def get_domains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetDomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def get_by_name_domains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetByNameParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GETBYNAME_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def upsert_domains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertDomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def delete_domains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteDomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

