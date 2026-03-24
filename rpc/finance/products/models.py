from pydantic import BaseModel


class FinanceProductItem1(BaseModel):
  recid: int | None = None
  sku: str
  name: str
  description: str | None = None
  category: str
  price: str
  currency: str
  credits: int
  enablement_key: str | None = None
  is_recurring: bool = False
  sort_order: int = 0
  status: int = 1
  created_on: str | None = None
  modified_on: str | None = None


class FinanceProductList1(BaseModel):
  products: list[FinanceProductItem1]


class FinanceProductFilter1(BaseModel):
  category: str | None = None
  status: int | None = None


class FinanceProductGet1(BaseModel):
  recid: int | None = None
  sku: str | None = None


class FinanceProductUpsert1(BaseModel):
  recid: int | None = None
  sku: str
  name: str
  description: str | None = None
  category: str
  price: str = "0"
  currency: str = "USD"
  credits: int = 0
  enablement_key: str | None = None
  is_recurring: bool = False
  sort_order: int = 0
  status: int = 1


class FinanceProductDelete1(BaseModel):
  recid: int


class FinanceProductDeleteResult1(BaseModel):
  recid: int
  deleted: bool
