from pydantic import BaseModel


class FinanceNumbersItem1(BaseModel):
  recid: int | None = None
  accounts_guid: str
  prefix: str | None = None
  account_number: str
  last_number: int = 0
  max_number: int | None = None
  allocation_size: int = 1
  reset_policy: str = "Never"
  sequence_status: int = 1
  pattern: str | None = None
  display_format: str | None = None
  account_name: str | None = None
  remaining: int | None = None


class FinanceNumbersList1(BaseModel):
  numbers: list[FinanceNumbersItem1]


class FinanceNumbersUpsert1(FinanceNumbersItem1):
  pass


class FinanceNumbersDelete1(BaseModel):
  recid: int


class FinanceNumbersNextNumber1(BaseModel):
  recid: int
