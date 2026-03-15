from pydantic import BaseModel


class FinancePeriodsItem1(BaseModel):
  guid: str | None = None
  year: int
  period_number: int
  period_name: str
  start_date: str
  end_date: str
  days_in_period: int
  quarter_number: int
  has_closing_week: bool = False
  is_leap_adjustment: bool = False
  anchor_event: str | None = None
  close_type: int = 0
  status: int = 1
  numbers_recid: int | None = None
  element_display_format: str | None = None


class FinancePeriodsList1(BaseModel):
  periods: list[FinancePeriodsItem1]


class FinancePeriodsListByYear1(BaseModel):
  year: int


class FinancePeriodsGet1(BaseModel):
  guid: str


class FinancePeriodsUpsert1(FinancePeriodsItem1):
  numbers_recid: int | None = None
  element_display_format: str | None = None


class FinancePeriodsDelete1(BaseModel):
  guid: str


class FinancePeriodsGenerateCalendar1(BaseModel):
  fiscal_year: int
  start_date: str
