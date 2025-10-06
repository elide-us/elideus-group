"""Users-domain MSSQL helpers for credit records."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_exec
from server.registry.types import DBResponse

__all__ = [
  "set_credits_v1",
]


def _build_update_sql() -> str:
  return """
    UPDATE users_credits
    SET element_credits = ?
    WHERE users_guid = ?;
  """


async def set_credits_v1(args: dict[str, Any]) -> DBResponse:
  sql = _build_update_sql()
  params = (args["credits"], args["guid"])
  return await run_exec(sql, params)
