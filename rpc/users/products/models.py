from pydantic import BaseModel


class UsersProductPurchase1(BaseModel):
  sku: str


class UsersProductPurchaseResult1(BaseModel):
  product: str
  transaction_token: str
  credits_granted: int | None = None
  lot_number: str | None = None
  enablement_granted: str | None = None


class UsersProductItem1(BaseModel):
  sku: str
  name: str
  description: str | None = None
  category: str
  price: str
  currency: str
  credits: int
  sort_order: int
  enablement_key: str | None = None
  already_enabled: bool = False


class UsersProductList1(BaseModel):
  products: list[UsersProductItem1]
