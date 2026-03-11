"""MSSQL implementations for finance credits query registry services."""

from __future__ import annotations

from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_one

__all__ = ["get_v1", "set_v1"]


async def get_v1(args: dict[str, Any]) -> DBResponse:
  sql = """
    SELECT users_guid, element_credits, element_reserve
    FROM users_credits
    WHERE users_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (args["guid"],))


async def set_v1(args: dict[str, Any]) -> DBResponse:
  sql = """
    UPDATE users_credits
    SET element_credits = ?
    WHERE users_guid = ?;
  """
  response = await run_exec(sql, (args["credits"], args["guid"]))
  return DBResponse(payload=response.payload, rowcount=response.rowcount)
