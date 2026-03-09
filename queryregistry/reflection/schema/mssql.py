"""MSSQL implementations for reflection schema query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse

__all__ = [
  "get_full_schema_v1",
  "list_columns_v1",
  "list_foreign_keys_v1",
  "list_indexes_v1",
  "list_tables_v1",
  "list_views_v1",
]


async def list_tables_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def list_columns_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def list_indexes_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def list_foreign_keys_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def list_views_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def get_full_schema_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")
