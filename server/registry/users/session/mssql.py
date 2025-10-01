"""MSSQL helpers for user session metadata."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "set_rotkey_v1",
]


def set_rotkey_v1(args: dict[str, Any]) -> Operation:
  guid = args["guid"]
  rotkey = args["rotkey"]
  iat = args["iat"]
  exp = args["exp"]
  sql = """
    UPDATE account_users
    SET element_rotkey = ?, element_rotkey_iat = ?, element_rotkey_exp = ?
    WHERE element_guid = ?;
  """
  return Operation(DbRunMode.EXEC, sql, (rotkey, iat, exp, guid))
