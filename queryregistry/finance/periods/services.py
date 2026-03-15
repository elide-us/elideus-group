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

_FISCAL_PERIODS_ACCOUNTS_GUID = "00000000-0000-0000-0000-000000000000"


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

  periods: list[dict[str, Any]] = []
  cursor = fy_start

  for quarter in range(1, 5):
    for month in range(1, 4):
      days = 28
      period_start = cursor
      period_end = cursor + timedelta(days=days - 1)

      periods.append(
        {
          "guid": str(uuid.uuid4()),
          "year": params.fiscal_year,
          "period_number": (quarter - 1) * 4 + month,
          "period_name": f"Q{quarter}M{month}",
          "start_date": period_start.isoformat(),
          "end_date": period_end.isoformat(),
          "days_in_period": days,
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

    mc_start = cursor
    mc_end = mc_start + timedelta(days=6)
    periods.append(
      {
        "guid": str(uuid.uuid4()),
        "year": params.fiscal_year,
        "period_number": quarter * 4,
        "period_name": f"Q{quarter}MC",
        "start_date": mc_start.isoformat(),
        "end_date": mc_end.isoformat(),
        "days_in_period": 7,
        "quarter_number": quarter,
        "has_closing_week": True,
        "is_leap_adjustment": False,
        "anchor_event": "period_close",
        "close_type": 0,
        "status": 1,
        "numbers_recid": numbers_recid,
      }
    )
    cursor = mc_end + timedelta(days=1)

  assert cursor == fy_start + timedelta(days=364)

  upsert_dispatcher = _select_dispatcher(provider, _UPSERT_DISPATCHERS)
  for period in periods:
    await upsert_dispatcher(period)

  result = await _select_dispatcher(provider, _LIST_BY_YEAR_DISPATCHERS)(
    {"year": params.fiscal_year}
  )
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
