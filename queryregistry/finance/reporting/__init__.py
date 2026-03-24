"""Finance reporting query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreditLotSummaryParams,
  JournalSummaryParams,
  PeriodStatusParams,
  TrialBalanceParams,
)

__all__ = [
  "credit_lot_summary_request",
  "journal_summary_request",
  "period_status_request",
  "trial_balance_request",
]


def trial_balance_request(params: TrialBalanceParams) -> DBRequest:
  return DBRequest(op="db:finance:reporting:trial_balance:1", payload=params.model_dump())


def journal_summary_request(params: JournalSummaryParams) -> DBRequest:
  return DBRequest(op="db:finance:reporting:journal_summary:1", payload=params.model_dump())


def period_status_request(params: PeriodStatusParams) -> DBRequest:
  return DBRequest(op="db:finance:reporting:period_status:1", payload=params.model_dump())


def credit_lot_summary_request(params: CreditLotSummaryParams) -> DBRequest:
  return DBRequest(op="db:finance:reporting:credit_lot_summary:1", payload=params.model_dump())
