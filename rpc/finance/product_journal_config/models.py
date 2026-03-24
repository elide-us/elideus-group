from pydantic import BaseModel


class FinanceProductJournalConfigItem1(BaseModel):
  recid: int
  category: str
  journal_scope: str
  journals_recid: int
  periods_guid: str
  approved_by: str | None = None
  approved_on: str | None = None
  activated_by: str | None = None
  activated_on: str | None = None
  status: int
  created_on: str | None = None
  modified_on: str | None = None


class FinanceProductJournalConfigList1(BaseModel):
  configs: list[FinanceProductJournalConfigItem1]


class FinanceProductJournalConfigFilter1(BaseModel):
  category: str | None = None
  periods_guid: str | None = None
  status: int | None = None


class FinanceProductJournalConfigGet1(BaseModel):
  recid: int


class FinanceProductJournalConfigUpsert1(BaseModel):
  recid: int | None = None
  category: str
  journal_scope: str
  journals_recid: int
  periods_guid: str
  status: int = 0


class FinanceProductJournalConfigApprove1(BaseModel):
  recid: int


class FinanceProductJournalConfigActivate1(BaseModel):
  recid: int


class FinanceProductJournalConfigClose1(BaseModel):
  recid: int
