"""System config query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import ConfigKeyParams, UpsertConfigParams

__all__ = [
  "delete_config_v1",
  "get_config_v1",
  "get_configs_v1",
  "upsert_config_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_GET_CONFIG_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_config_v1}
_GET_CONFIGS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_configs_v1}
_UPSERT_CONFIG_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_config_v1}
_DELETE_CONFIG_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_config_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system config registry")
  return dispatcher


async def get_config_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ConfigKeyParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_CONFIG_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_configs_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _GET_CONFIGS_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_config_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertConfigParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_CONFIG_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_config_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ConfigKeyParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_CONFIG_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
