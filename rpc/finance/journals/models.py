from pydantic import BaseModel, Field


class JournalItem1(BaseModel):
  recid: int | None = None
  name: str
  description: str | None = None
  posting_key: str | None = None
  source_type: str | None = None
  source_id: str | None = None
  periods_guid: str | None = None
  ledgers_recid: int | None = None
  numbers_recid: int | None = None
  status: int = 0
  posted_by: str | None = None
  posted_on: str | None = None
  reversed_by: int | None = None
  reversal_of: int | None = None


class JournalList1(BaseModel):
  journals: list[JournalItem1]


class JournalGet1(BaseModel):
  recid: int


class JournalLineItem1(BaseModel):
  recid: int | None = None
  journals_recid: int
  line_number: int
  accounts_guid: str
  debit: str = "0"
  credit: str = "0"
  description: str | None = None
  dimension_recids: list[int] = Field(default_factory=list)


class JournalLineList1(BaseModel):
  lines: list[JournalLineItem1]


class JournalGetLines1(BaseModel):
  journals_recid: int


class JournalCreateLine1(BaseModel):
  line_number: int
  accounts_guid: str
  debit: str = "0"
  credit: str = "0"
  description: str | None = None
  dimension_recids: list[int] = Field(default_factory=list)


class JournalCreate1(BaseModel):
  name: str
  description: str | None = None
  posting_key: str | None = None
  source_type: str | None = None
  source_id: str | None = None
  periods_guid: str | None = None
  ledgers_recid: int | None = None
  lines: list[JournalCreateLine1]


class JournalListFilter1(BaseModel):
  status: int | None = None
  periods_guid: str | None = None


class JournalSubmitForApproval1(BaseModel):
  recid: int


class JournalApprove1(BaseModel):
  recid: int


class JournalReject1(BaseModel):
  recid: int
  reason: str | None = None


class JournalReverse1(BaseModel):
  recid: int
