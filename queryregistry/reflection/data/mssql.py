"""MSSQL implementations for reflection data query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse

__all__ = [
  "apply_batch_v1",
  "dump_table_v1",
  "get_version_v1",
  "rebuild_indexes_v1",
  "update_version_v1",
]


async def get_version_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def update_version_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def dump_table_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def rebuild_indexes_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")


async def apply_batch_v1(_: Mapping[str, Any]) -> DBResponse:
  raise NotImplementedError("Not yet migrated from database_cli_module")
