from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  DeleteVendorParams,
  GetVendorByNameParams,
  GetVendorParams,
  ListVendorsParams,
  UpsertVendorParams,
)

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance vendors registry")
  return dispatcher


async def list_vendors_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListVendorsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.list_vendors_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_vendor_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetVendorParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.get_vendor_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_vendor_by_name_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetVendorByNameParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.get_vendor_by_name_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_vendor_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertVendorParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.upsert_vendor_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_vendor_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteVendorParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, {"mssql": mssql.delete_vendor_v1})(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
