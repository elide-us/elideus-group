"""Finance products query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeleteProductParams",
  "GetProductParams",
  "ListProductsParams",
  "UpsertProductParams",
]


class ListProductsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  category: str | None = None
  status: int | None = None


class GetProductParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  sku: str | None = None


class UpsertProductParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

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


class DeleteProductParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
