from pydantic import BaseModel


class CreditLotItem1(BaseModel):
  recid: int | None = None
  users_guid: str
  lot_number: str | None = None
  source_type: str
  credits_original: int
  credits_remaining: int
  unit_price: str = "0"
  total_paid: str = "0"
  currency: str = "USD"
  expires_at: str | None = None
  expired: bool = False
  source_id: str | None = None
  numbers_recid: int | None = None
  status: int = 1


class CreditLotList1(BaseModel):
  lots: list[CreditLotItem1]


class CreditLotListByUser1(BaseModel):
  users_guid: str


class CreditLotGet1(BaseModel):
  recid: int


class CreditLotCreate1(BaseModel):
  users_guid: str
  source_type: str
  credits: int
  total_paid: str = "0"
  currency: str = "USD"
  expires_at: str | None = None
  source_id: str | None = None


class CreditLotConsume1(BaseModel):
  users_guid: str
  credits_needed: int
  service_type: str | None = None
  description: str | None = None
  periods_guid: str | None = None


class CreditLotExpire1(BaseModel):
  recid: int


class CreditLotListEvents1(BaseModel):
  lots_recid: int


class CreditLotEventItem1(BaseModel):
  recid: int | None = None
  lots_recid: int
  event_type: str
  credits: int
  unit_price: str = "0"
  description: str | None = None
  actor_guid: str | None = None
  journals_recid: int | None = None


class CreditLotEventList1(BaseModel):
  events: list[CreditLotEventItem1]


class CreditLotWalletBalance1(BaseModel):
  users_guid: str


class CreditLotWalletResult1(BaseModel):
  users_guid: str
  balance: int


class CreditLotConsumeResult1(BaseModel):
  credits_consumed: int
  lots_affected: int
  journal_recid: int | None = None
