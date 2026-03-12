"""Finance periods query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import date, timedelta
from typing import Any
import uuid

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  DeletePeriodParams,
  GenerateCalendarParams,
  GetPeriodParams,
  ListPeriodsByYearParams,
  ListPeriodsParams,
  UpsertPeriodParams,
)

__all__ = [
  "delete_v1",
  "generate_calendar_v1",
  "get_v1",
  "list_by_year_v1",
  "list_v1",
  "upsert_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_LIST_BY_YEAR_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_year_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance periods registry")
  return dispatcher


def _fiscal_year_has_feb_29(fy_start: date) -> bool:
  fy_end = fy_start + timedelta(days=364)
  for year in {fy_start.year, fy_end.year}:
    try:
      feb29 = date(year, 2, 29)
    except ValueError:
      continue
    if fy_start <= feb29 <= fy_end:
      return True
  return False


async def list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListPeriodsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_by_year_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListPeriodsByYearParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_BY_YEAR_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetPeriodParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertPeriodParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeletePeriodParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def generate_calendar_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GenerateCalendarParams.model_validate(request.payload)
  fy_start = date.fromisoformat(params.start_date)
  if fy_start.weekday() != 6:
    raise ValueError("Fiscal year start_date must be a Sunday")

  is_leap = _fiscal_year_has_feb_29(fy_start)
  periods: list[dict[str, Any]] = []
  cursor = fy_start

  for quarter in range(1, 5):
    for month in range(1, 5):
      days = 28 if month <= 3 else 7
      if is_leap and quarter == 1 and month == 4:
        days = 8
      period_start = cursor
      period_end = cursor + timedelta(days=days - 1)

      periods.append(
        {
          "guid": str(uuid.uuid4()),
          "year": params.fiscal_year,
          "period_number": (quarter - 1) * 5 + month,
          "period_name": f"Q{quarter}M{month}",
          "start_date": period_start.isoformat(),
          "end_date": period_end.isoformat(),
          "days_in_period": days,
          "quarter_number": quarter,
          "has_closing_week": False,
          "is_leap_adjustment": is_leap and quarter == 1 and month == 4,
          "anchor_event": None,
          "close_type": 0,
          "status": 1,
        }
      )
      cursor = period_end + timedelta(days=1)

    periods.append(
      {
        "guid": str(uuid.uuid4()),
        "year": params.fiscal_year,
        "period_number": (quarter - 1) * 5 + 5,
        "period_name": f"Q{quarter}MC",
        "start_date": (cursor - timedelta(days=7)).isoformat(),
        "end_date": (cursor - timedelta(days=1)).isoformat(),
        "days_in_period": 0,
        "quarter_number": quarter,
        "has_closing_week": True,
        "is_leap_adjustment": False,
        "anchor_event": "period_close",
        "close_type": 0,
        "status": 1,
      }
    )

  upsert_dispatcher = _select_dispatcher(provider, _UPSERT_DISPATCHERS)
  for period in periods:
    await upsert_dispatcher(period)

  result = await _select_dispatcher(provider, _LIST_BY_YEAR_DISPATCHERS)(
    {"year": params.fiscal_year}
  )
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
