"""RPC dispatch subdomains query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import ListSubdomainsParams, GetSubdomainParams, ListByDomainParams, UpsertSubdomainParams, DeleteSubdomainParams

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_subdomains_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_subdomain_v1}
_LISTBYDOMAIN_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_domain_subdomains_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_subdomain_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_subdomain_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for rpcdispatch subdomains registry")
  return dispatcher

async def list_subdomains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListSubdomainsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def get_subdomains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetSubdomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def list_by_domain_subdomains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListByDomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LISTBYDOMAIN_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def upsert_subdomains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertSubdomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def delete_subdomains_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteSubdomainParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

