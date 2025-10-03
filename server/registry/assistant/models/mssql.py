"""Assistant model queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_json_many, run_json_one
from server.registry.types import DBResponse

__all__ = [
  "get_by_name_v1",
  "list_models_v1",
]


async def list_models_v1(_: dict[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name AS name
    FROM assistant_models
    ORDER BY element_name
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def get_by_name_v1(args: dict[str, Any]) -> DBResponse:
  name = args["name"]
  sql = """
    SELECT recid FROM assistant_models WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (name,))
