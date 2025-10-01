"""System configuration helpers for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DBResult, DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import (
  Operation,
  exec_op,
  exec_query,
)

__all__ = [
  "delete_config_v1",
  "get_config_v1",
  "get_configs_v1",
  "upsert_config_v1",
]


def get_config_v1(args: dict[str, Any]) -> Operation:
  key = args["key"]
  sql = """
    SELECT element_value AS value
    FROM system_config
    WHERE element_key = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(DbRunMode.JSON_ONE, sql, (key,))


async def upsert_config_v1(args: dict[str, Any]) -> DBResult:
  key = args["key"]
  value = args["value"]
  rc = await exec_query(exec_op(
    "UPDATE system_config SET element_value = ? WHERE element_key = ?;",
    (value, key),
  ))
  if rc.rowcount == 0:
    rc = await exec_query(exec_op(
      "INSERT INTO system_config (element_key, element_value) VALUES (?, ?);",
      (key, value),
    ))
  return rc


def get_configs_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT element_key AS [key], element_value AS value
    FROM system_config
    ORDER BY element_key
    FOR JSON PATH;
  """
  return Operation(DbRunMode.JSON_MANY, sql, ())


def delete_config_v1(args: dict[str, Any]) -> Operation:
  key = args["key"]
  sql = "DELETE FROM system_config WHERE element_key = ?;"
  return Operation(DbRunMode.EXEC, sql, (key,))
