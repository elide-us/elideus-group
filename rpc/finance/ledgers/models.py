from pydantic import BaseModel


class FinanceLedgersItem1(BaseModel):
  recid: int
  element_name: str
  element_description: str | None = None
  element_fiscal_calendar_year: int | None = None
  element_chart_of_accounts_guid: str | None = None
  element_status: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class FinanceLedgersList1(BaseModel):
  ledgers: list[FinanceLedgersItem1]


class FinanceLedgersGet1(BaseModel):
  recid: int


class FinanceLedgersCreate1(BaseModel):
  element_name: str
  element_description: str | None = None
  element_fiscal_calendar_year: int | None = None
  element_chart_of_accounts_guid: str | None = None


class FinanceLedgersUpdate1(BaseModel):
  recid: int
  element_name: str
  element_description: str | None = None
  element_fiscal_calendar_year: int | None = None
  element_chart_of_accounts_guid: str | None = None
  element_status: int = 1


class FinanceLedgersDelete1(BaseModel):
  recid: int
