"""MSSQL helpers for account metadata queries."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "account_exists_v1",
]


def account_exists_v1(args: dict[str, Any]) -> Operation:
  guid = str(UUID(args["user_guid"]))
  sql = """
    SELECT 1 AS exists_flag
    FROM account_users
    WHERE element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(DbRunMode.JSON_ONE, sql, (guid,))
