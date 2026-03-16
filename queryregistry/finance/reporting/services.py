"""Finance reporting query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreditLotSummaryParams,
  JournalSummaryParams,
  PeriodStatusParams,
  TrialBalanceParams,
)

__all__ = [
  "credit_lot_summary_v1",
  "journal_summary_v1",
  "period_status_v1",
  "trial_balance_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_TRIAL_BALANCE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.trial_balance_v1}
_JOURNAL_SUMMARY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.journal_summary_v1}
_PERIOD_STATUS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.period_status_v1}
_CREDIT_LOT_SUMMARY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.credit_lot_summary_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance reporting registry")
  return dispatcher


async def trial_balance_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = TrialBalanceParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _TRIAL_BALANCE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def journal_summary_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = JournalSummaryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _JOURNAL_SUMMARY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def period_status_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = PeriodStatusParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _PERIOD_STATUS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def credit_lot_summary_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreditLotSummaryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREDIT_LOT_SUMMARY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
