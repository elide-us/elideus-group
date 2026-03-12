from pydantic import BaseModel


class FinanceNumbersItem1(BaseModel):
  recid: int | None = None
  accounts_guid: str
  prefix: str | None = None
  account_number: str
  last_number: int = 1000
  allocation_size: int = 10
  reset_policy: str = "Never"
  pattern: str | None = None
  display_format: str | None = None
  account_name: str | None = None


class FinanceNumbersList1(BaseModel):
  numbers: list[FinanceNumbersItem1]


class FinanceNumbersUpsert1(FinanceNumbersItem1):
  pattern: str | None = None
  display_format: str | None = None


class FinanceNumbersDelete1(BaseModel):
  recid: int


class FinanceNumbersNextNumber1(BaseModel):
  recid: int
