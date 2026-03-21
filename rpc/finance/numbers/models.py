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
  sequence_type: str = "continuous"
  series_number: int = 1
  scope: str | None = None
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


class FinanceNumbersShift1(BaseModel):
  current_recid: int
  new_prefix: str | None = None
  new_account_number: str
  new_display_format: str | None = None
  new_pattern: str | None = None
  new_allocation_size: int = 1


class FinanceNumbersShiftResult1(BaseModel):
  closed_sequence: FinanceNumbersItem1 | None = None
  new_sequence: FinanceNumbersItem1
