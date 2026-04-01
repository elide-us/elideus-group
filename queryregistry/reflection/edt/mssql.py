"""MSSQL implementations for reflection EDT query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many

__all__ = ["list_edt_v1"]


async def list_edt_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT recid, element_name
    FROM system_edt_mappings
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)
