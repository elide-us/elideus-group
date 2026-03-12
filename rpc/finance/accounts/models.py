from pydantic import BaseModel


class FinanceAccountsItem1(BaseModel):
  guid: str | None = None
  number: str
  name: str
  account_type: int
  parent: str | None = None
  is_posting: bool = True
  status: int = 1


class FinanceAccountsList1(BaseModel):
  accounts: list[FinanceAccountsItem1]


class FinanceAccountsGet1(BaseModel):
  guid: str


class FinanceAccountsListChildren1(BaseModel):
  parent_guid: str


class FinanceAccountsUpsert1(FinanceAccountsItem1):
  pass


class FinanceAccountsDelete1(BaseModel):
  guid: str
