"""Finance credit lots query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateEventParams,
  CreateLotParams,
  ConsumeCreditsParams,
  ExpireLotParams,
  GetLotParams,
  ListEventsByLotParams,
  ListLotsByUserParams,
  SumRemainingByUserParams,
)

__all__ = [
  "consume_credits_v1",
  "create_event_v1",
  "create_lot_v1",
  "expire_lot_v1",
  "get_lot_v1",
  "list_events_by_lot_v1",
  "list_lots_by_user_v1",
  "sum_remaining_by_user_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_LOTS_BY_USER_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_lots_by_user_v1}
_GET_LOT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_lot_v1}
_CREATE_LOT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_lot_v1}
_CONSUME_CREDITS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.consume_credits_v1}
_EXPIRE_LOT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.expire_lot_v1}
_LIST_EVENTS_BY_LOT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_events_by_lot_v1}
_CREATE_EVENT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_event_v1}
_SUM_REMAINING_BY_USER_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.sum_remaining_by_user_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance credit lots registry")
  return dispatcher


async def list_lots_by_user_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListLotsByUserParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_LOTS_BY_USER_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_lot_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetLotParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_LOT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_lot_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateLotParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_LOT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def consume_credits_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ConsumeCreditsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CONSUME_CREDITS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def expire_lot_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ExpireLotParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _EXPIRE_LOT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_events_by_lot_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListEventsByLotParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_EVENTS_BY_LOT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_event_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateEventParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_EVENT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def sum_remaining_by_user_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SumRemainingByUserParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _SUM_REMAINING_BY_USER_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
