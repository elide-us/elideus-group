"""Finance periods query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import date, timedelta
from typing import Any
import uuid

from queryregistry.models import DBRequest, DBResponse

from queryregistry.finance.numbers.models import GetByPrefixAndAccountNumberParams, UpsertNumberParams
from queryregistry.finance.numbers.services import get_by_prefix_account_v1 as get_number_by_prefix_account_v1
from queryregistry.finance.numbers.services import upsert_v1 as upsert_number_v1

from . import mssql
from .models import (
  ClosePeriodParams,
  DeletePeriodParams,
  GenerateCalendarParams,
  GetPeriodParams,
  ListPeriodCloseBlockersParams,
  ListPeriodsByYearParams,
  ListPeriodsParams,
  LockPeriodParams,
  ReopenPeriodParams,
  UnlockPeriodParams,
  UpsertPeriodParams,
)

__all__ = [
  "close_v1",
  "delete_v1",
  "generate_calendar_v1",
  "get_v1",
  "list_by_year_v1",
  "list_close_blockers_v1",
  "list_v1",
  "lock_v1",
  "reopen_v1",
  "unlock_v1",
  "upsert_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_v1}
_LIST_BY_YEAR_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_year_v1}
_GET_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_v1}
_CLOSE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.close_period_v1}
_REOPEN_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.reopen_period_v1}
_LOCK_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.lock_period_v1}
_UNLOCK_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.unlock_period_v1}
_LIST_CLOSE_BLOCKERS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_close_blockers_v1}
_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_v1}
_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_v1}

_FISCAL_PERIODS_ACCOUNTS_GUID = "00000000-0000-0000-0000-000000000000"


def _nearest_sunday_for_fiscal_year(fiscal_year: int) -> date:
  target = date(fiscal_year - 1, 12, 28)
  nearest: date | None = None
  nearest_distance: int | None = None

  for offset in range(-6, 7):
    candidate = target + timedelta(days=offset)
    if candidate.weekday() != 6:
      continue
    distance = abs(offset)
    if nearest is None or nearest_distance is None or distance < nearest_distance or (distance == nearest_distance and candidate < nearest):
      nearest = candidate
      nearest_distance = distance

  if nearest is None:
    raise ValueError(f"Unable to resolve fiscal year start for {fiscal_year}")
  return nearest


def _build_calendar_periods(fiscal_year: int, start_date_value: str | None, numbers_recid: int) -> list[dict[str, Any]]:
  fy_start = date.fromisoformat(start_date_value) if start_date_value else _nearest_sunday_for_fiscal_year(fiscal_year)
  if fy_start.weekday() != 6:
    raise ValueError("Fiscal year start_date must be a Sunday")

  next_fy_start = _nearest_sunday_for_fiscal_year(fiscal_year + 1)
  fiscal_year_days = (next_fy_start - fy_start).days
  if fiscal_year_days not in {364, 371}:
    raise ValueError(f"Fiscal year {fiscal_year} produced unsupported length {fiscal_year_days}")

  periods: list[dict[str, Any]] = []
  cursor = fy_start
  period_number = 1

  for quarter in range(1, 5):
    for month in range(1, 4):
      period_end = cursor + timedelta(days=27)
      periods.append(
        {
          "guid": str(uuid.uuid4()),
          "year": fiscal_year,
          "period_number": period_number,
          "period_name": f"Q{quarter}M{month}",
          "start_date": cursor.isoformat(),
          "end_date": period_end.isoformat(),
          "days_in_period": 28,
          "quarter_number": quarter,
          "has_closing_week": False,
          "is_leap_adjustment": False,
          "anchor_event": None,
          "close_type": 0,
          "status": 1,
          "numbers_recid": numbers_recid,
        }
      )
      cursor = period_end + timedelta(days=1)
      period_number += 1

    closing_days = 14 if quarter == 4 and fiscal_year_days == 371 else 7
    closing_end = cursor + timedelta(days=closing_days - 1)
    periods.append(
      {
        "guid": str(uuid.uuid4()),
        "year": fiscal_year,
        "period_number": period_number,
        "period_name": f"Q{quarter}MC",
        "start_date": cursor.isoformat(),
        "end_date": closing_end.isoformat(),
        "days_in_period": closing_days,
        "quarter_number": quarter,
        "has_closing_week": True,
        "is_leap_adjustment": quarter == 4 and fiscal_year_days == 371,
        "anchor_event": "period_close",
        "close_type": 2 if quarter == 4 else 1,
        "status": 1,
        "numbers_recid": numbers_recid,
      }
    )
    cursor = closing_end + timedelta(days=1)
    period_number += 1

  if cursor != fy_start + timedelta(days=fiscal_year_days):
    raise ValueError(f"Generated fiscal year {fiscal_year} length { (cursor - fy_start).days } instead of {fiscal_year_days}")

  return periods


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance periods registry")
  return dispatcher


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


async def close_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ClosePeriodParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CLOSE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def reopen_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ReopenPeriodParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _REOPEN_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def lock_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = LockPeriodParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LOCK_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def unlock_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UnlockPeriodParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UNLOCK_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_close_blockers_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListPeriodCloseBlockersParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_CLOSE_BLOCKERS_DISPATCHERS)(params.model_dump())
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

  existing = await list_by_year_v1(
    DBRequest(
      op="db:finance:periods:list_by_year:1",
      payload=ListPeriodsByYearParams(year=params.fiscal_year).model_dump(),
    ),
    provider=provider,
  )
  if existing.rows:
    raise ValueError(f"Fiscal year {params.fiscal_year} already has generated periods")

  lookup_request = DBRequest(
    op="db:finance:numbers:get_by_prefix_account:1",
    payload=GetByPrefixAndAccountNumberParams(
      prefix="FP",
      account_number=str(params.fiscal_year),
    ).model_dump(),
  )
  number_result = await get_number_by_prefix_account_v1(lookup_request, provider=provider)

  number_payload = number_result.payload if isinstance(number_result.payload, dict) else None
  if number_payload and number_payload.get("recid") is not None:
    numbers_recid = int(number_payload["recid"])
  else:
    upsert_request = DBRequest(
      op="db:finance:numbers:upsert:1",
      payload=UpsertNumberParams(
        accounts_guid=_FISCAL_PERIODS_ACCOUNTS_GUID,
        prefix="FP",
        account_number=str(params.fiscal_year),
        last_number=0,
        allocation_size=1,
        reset_policy="Never",
        display_format=f"FY{params.fiscal_year}",
      ).model_dump(),
    )
    upsert_result = await upsert_number_v1(upsert_request, provider=provider)
    upsert_payload = upsert_result.payload if isinstance(upsert_result.payload, dict) else None
    if not upsert_payload or upsert_payload.get("recid") is None:
      raise ValueError(f"Failed to create number sequence for fiscal year {params.fiscal_year}")
    numbers_recid = int(upsert_payload["recid"])

  periods = _build_calendar_periods(params.fiscal_year, params.start_date, numbers_recid)

  upsert_dispatcher = _select_dispatcher(provider, _UPSERT_DISPATCHERS)
  for period in periods:
    await upsert_dispatcher(period)

  result = await _select_dispatcher(provider, _LIST_BY_YEAR_DISPATCHERS)({
    "year": params.fiscal_year
  })
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
