"""Discord channels query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  BumpChannelActivityParams,
  ChannelIdParams,
  ListChannelsByGuildParams,
  UpsertChannelParams,
)

__all__ = [
  "bump_activity_v1",
  "get_channel_v1",
  "list_by_guild_v1",
  "upsert_channel_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_channel_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_channel_v1}
_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_guild_v1}
_BUMP_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.bump_activity_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for discord channels registry")
  return dispatcher


async def upsert_channel_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertChannelParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_channel_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ChannelIdParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_by_guild_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListChannelsByGuildParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def bump_activity_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = BumpChannelActivityParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _BUMP_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
