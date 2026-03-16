"""Finance reporting query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CreditLotSummaryParams",
  "CreditLotSummaryRecord",
  "JournalSummaryParams",
  "JournalSummaryRecord",
  "PeriodStatusParams",
  "PeriodStatusRecord",
  "TrialBalanceParams",
  "TrialBalanceRecord",
]


class TrialBalanceParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  fiscal_year: int | None = None
  period_guid: str | None = None


class JournalSummaryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  journal_status: int | None = None
  fiscal_year: int | None = None
  periods_guid: str | None = None


class PeriodStatusParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  fiscal_year: int | None = None


class CreditLotSummaryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  users_guid: str | None = None


class TrialBalanceRecord(TypedDict):
  period_guid: str
  fiscal_year: int
  period_number: int
  period_name: str
  account_guid: str
  account_number: str
  account_name: str
  account_type: int
  total_debit: str
  total_credit: str
  net_balance: str


class JournalSummaryRecord(TypedDict):
  recid: int
  journal_name: str
  journal_description: str | None
  posting_key: str | None
  source_type: str | None
  source_id: str | None
  journal_status: int
  periods_guid: str | None
  fiscal_year: int | None
  period_name: str | None
  posted_by: str | None
  posted_on: str | None
  reversed_by: int | None
  reversal_of: int | None
  created_on: str
  line_count: int
  total_debit: str
  total_credit: str


class PeriodStatusRecord(TypedDict):
  period_guid: str
  fiscal_year: int
  period_number: int
  period_name: str
  start_date: str
  end_date: str
  close_type: int
  period_status: int
  has_closing_week: bool
  total_journals: int
  unposted_journals: int
  posted_journals: int
  reversed_journals: int


class CreditLotSummaryRecord(TypedDict):
  recid: int
  users_guid: str
  user_display_name: str
  lot_number: str
  source_type: str
  credits_original: int
  credits_remaining: int
  unit_price: str
  total_paid: str
  currency: str
  expires_at: str | None
  expired: bool
  source_id: str | None
  lot_status: int
  created_on: str
  event_count: int
  total_consumed: int
