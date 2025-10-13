"""System configuration helpers for MSSQL."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_exec, run_json_many, run_json_one
from server.registry.types import DBResponse

__all__ = [
  "delete_config_v1",
  "get_config_v1",
  "get_configs_v1",
  "upsert_config_v1",
]


async def get_config_v1(args: dict[str, Any]) -> DBResponse:
  key = args["key"]
  sql = """
    SELECT element_value AS value
    FROM system_config
    WHERE element_key = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (key,))


async def upsert_config_v1(args: dict[str, Any]) -> DBResponse:
  key = args["key"]
  value = args["value"]
  rc = await run_exec("UPDATE system_config SET element_value = ? WHERE element_key = ?;", (value, key))
  if rc.rowcount == 0:
    rc = await run_exec(
      "INSERT INTO system_config (element_key, element_value) VALUES (?, ?);",
      (key, value),
    )
  return rc


async def get_configs_v1(_: dict[str, Any]) -> DBResponse:
  sql = """
    SELECT element_key AS [key], element_value AS value
    FROM system_config
    ORDER BY element_key
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def delete_config_v1(args: dict[str, Any]) -> DBResponse:
  key = args["key"]
  sql = "DELETE FROM system_config WHERE element_key = ?;"
  return await run_exec(sql, (key,))
