"""Assistant model queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "get_by_name_v1",
  "list_models_v1",
]


def list_models_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT
      recid,
      element_name AS name
    FROM assistant_models
    ORDER BY element_name
    FOR JSON PATH;
  """
  return Operation(DbRunMode.JSON_MANY, sql, ())


def get_by_name_v1(args: dict[str, Any]) -> Operation:
  name = args["name"]
  sql = """
    SELECT recid FROM assistant_models WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(DbRunMode.JSON_ONE, sql, (name,))
