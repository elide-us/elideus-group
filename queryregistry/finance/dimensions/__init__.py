"""Finance dimensions query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeleteDimensionParams,
  GetDimensionParams,
  ListDimensionsByNameParams,
  ListDimensionsParams,
  UpsertDimensionParams,
)

__all__ = [
  "delete_dimension_request",
  "get_dimension_request",
  "list_dimensions_by_name_request",
  "list_dimensions_request",
  "upsert_dimension_request",
]


def list_dimensions_request(params: ListDimensionsParams) -> DBRequest:
  return DBRequest(op="db:finance:dimensions:list:1", payload=params.model_dump())


def list_dimensions_by_name_request(params: ListDimensionsByNameParams) -> DBRequest:
  return DBRequest(op="db:finance:dimensions:list_by_name:1", payload=params.model_dump())


def get_dimension_request(params: GetDimensionParams) -> DBRequest:
  return DBRequest(op="db:finance:dimensions:get:1", payload=params.model_dump())


def upsert_dimension_request(params: UpsertDimensionParams) -> DBRequest:
  return DBRequest(op="db:finance:dimensions:upsert:1", payload=params.model_dump())


def delete_dimension_request(params: DeleteDimensionParams) -> DBRequest:
  return DBRequest(op="db:finance:dimensions:delete:1", payload=params.model_dump())
