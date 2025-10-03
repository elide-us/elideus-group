"""Support-domain MSSQL helpers for user records."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_exec
from server.registry.types import DBResponse

__all__ = [
  "set_credits_v1",
]


async def set_credits_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  credits = args["credits"]
  sql = """
    UPDATE users_credits
    SET element_credits = ?
    WHERE users_guid = ?;
  """
  return await run_exec(sql, (credits, guid))
