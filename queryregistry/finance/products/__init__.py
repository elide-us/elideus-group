"""Finance products query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteProductParams, GetProductParams, ListProductsParams, UpsertProductParams

__all__ = [
  "delete_product_request",
  "get_product_request",
  "list_products_request",
  "upsert_product_request",
]


def list_products_request(params: ListProductsParams) -> DBRequest:
  return DBRequest(op="db:finance:products:list:1", payload=params.model_dump())


def get_product_request(params: GetProductParams) -> DBRequest:
  return DBRequest(op="db:finance:products:get:1", payload=params.model_dump())


def upsert_product_request(params: UpsertProductParams) -> DBRequest:
  return DBRequest(op="db:finance:products:upsert:1", payload=params.model_dump())


def delete_product_request(params: DeleteProductParams) -> DBRequest:
  return DBRequest(op="db:finance:products:delete:1", payload=params.model_dump())
