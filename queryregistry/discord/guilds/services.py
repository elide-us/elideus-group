"""Discord guilds query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import GuildIdParams, ListGuildsParams, UpdateGuildCreditsParams, UpsertGuildParams

__all__ = [
  "get_guild_v1",
  "list_guilds_v1",
  "update_credits_v1",
  "upsert_guild_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_guild_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_guild_v1}
_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_guilds_v1}
_UPDATE_CREDITS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_credits_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for discord guilds registry")
  return dispatcher


async def upsert_guild_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertGuildParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_guild_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GuildIdParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_guilds_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListGuildsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_credits_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateGuildCreditsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_CREDITS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
