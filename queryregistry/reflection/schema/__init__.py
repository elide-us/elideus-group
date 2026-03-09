"""Reflection schema query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import ColumnParams, TableParams

__all__ = [
  "get_full_schema_request",
  "list_columns_request",
  "list_foreign_keys_request",
  "list_indexes_request",
  "list_tables_request",
  "list_views_request",
]


def list_tables_request() -> DBRequest:
  return DBRequest(op="db:reflection:schema:list_tables:1", payload={})


def list_columns_request(params: TableParams) -> DBRequest:
  return DBRequest(op="db:reflection:schema:list_columns:1", payload=params.model_dump())


def list_indexes_request(params: TableParams) -> DBRequest:
  return DBRequest(op="db:reflection:schema:list_indexes:1", payload=params.model_dump())


def list_foreign_keys_request(params: TableParams) -> DBRequest:
  return DBRequest(op="db:reflection:schema:list_foreign_keys:1", payload=params.model_dump())


def list_views_request() -> DBRequest:
  return DBRequest(op="db:reflection:schema:list_views:1", payload={})


def get_full_schema_request(params: ColumnParams | None = None) -> DBRequest:
  payload = {} if params is None else params.model_dump()
  return DBRequest(op="db:reflection:schema:get_full_schema:1", payload=payload)
