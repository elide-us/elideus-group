"""MSSQL implementations for system models query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_json_many, run_json_one

from queryregistry.models import DBResponse

__all__ = [
  "get_by_name_v1",
  "list_v1",
]


async def list_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name AS name
    FROM assistant_models
    ORDER BY element_name
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def get_by_name_v1(args: Mapping[str, Any]) -> DBResponse:
  name = args["name"]
  sql = """
    SELECT recid
    FROM assistant_models
    WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (name,))
