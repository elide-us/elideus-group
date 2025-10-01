"""Support-domain MSSQL helpers for user records."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "set_credits_v1",
]


def set_credits_v1(args: dict[str, Any]) -> Operation:
  guid = args["guid"]
  credits = args["credits"]
  sql = """
    UPDATE users_credits
    SET element_credits = ?
    WHERE users_guid = ?;
  """
  return Operation(DbRunMode.EXEC, sql, (credits, guid))
