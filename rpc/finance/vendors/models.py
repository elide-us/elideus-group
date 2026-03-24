from pydantic import BaseModel


class FinanceVendorItem1(BaseModel):
  recid: int | None = None
  element_name: str
  element_display: str | None = None
  element_description: str | None = None
  element_status: int = 1


class FinanceVendorList1(BaseModel):
  vendors: list[FinanceVendorItem1]


class FinanceVendorUpsert1(BaseModel):
  recid: int | None = None
  element_name: str
  element_display: str | None = None
  element_description: str | None = None
  element_status: int = 1


class FinanceVendorDelete1(BaseModel):
  recid: int


class FinanceVendorDeleteResult1(BaseModel):
  recid: int
  deleted: bool
