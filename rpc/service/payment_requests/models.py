"""Service payment requests RPC models."""

from pydantic import BaseModel


class PaymentRequestCreate1(BaseModel):
  vendor_name: str
  amount: str
  currency: str = "USD"
  description: str
  service: str | None = None
  category: str | None = None
  period_start: str
  period_end: str
  renewal_recid: int | None = None


class PaymentRequestCreateResult1(BaseModel):
  import_recid: int
  status: str
  message: str
