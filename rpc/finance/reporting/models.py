from pydantic import BaseModel


class TrialBalanceFilter1(BaseModel):
  fiscal_year: int | None = None
  period_guid: str | None = None


class JournalSummaryFilter1(BaseModel):
  journal_status: int | None = None
  fiscal_year: int | None = None
  periods_guid: str | None = None


class PeriodStatusFilter1(BaseModel):
  fiscal_year: int | None = None


class CreditLotSummaryFilter1(BaseModel):
  users_guid: str | None = None


class TrialBalanceList1(BaseModel):
  rows: list[dict]


class JournalSummaryList1(BaseModel):
  journals: list[dict]


class PeriodStatusList1(BaseModel):
  periods: list[dict]


class CreditLotSummaryList1(BaseModel):
  lots: list[dict]
