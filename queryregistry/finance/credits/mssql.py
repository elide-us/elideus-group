"""MSSQL implementations for finance credits query registry services."""

from __future__ import annotations

from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec

__all__ = ["set_v1"]


async def set_v1(args: dict[str, Any]) -> DBResponse:
  sql = """
    UPDATE users_credits
    SET element_credits = ?
    WHERE users_guid = ?;
  """
  response = await run_exec(sql, (args["credits"], args["guid"]))
  return DBResponse(payload=response.payload, rowcount=response.rowcount)
