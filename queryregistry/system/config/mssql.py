"""MSSQL implementations for system config query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from queryregistry.models import DBResponse

__all__ = [
  "delete_config_v1",
  "get_config_v1",
  "get_configs_v1",
  "upsert_config_v1",
]


async def get_config_v1(args: Mapping[str, Any]) -> DBResponse:
  key = args["key"]
  sql = """
    SELECT element_value
    FROM system_config
    WHERE element_key = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (key,))


async def get_configs_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT element_key, element_value
    FROM system_config
    ORDER BY element_key
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def upsert_config_v1(args: Mapping[str, Any]) -> DBResponse:
  key = args["key"]
  value = args["value"]
  sql = """
    MERGE system_config AS target
    USING (SELECT ? AS element_key, ? AS element_value) AS src
    ON target.element_key = src.element_key
    WHEN MATCHED THEN
      UPDATE SET element_value = src.element_value
    WHEN NOT MATCHED THEN
      INSERT (element_key, element_value)
      VALUES (src.element_key, src.element_value);
  """
  return await run_exec(sql, (key, value))


async def delete_config_v1(args: Mapping[str, Any]) -> DBResponse:
  key = args["key"]
  sql = "DELETE FROM system_config WHERE element_key = ?;"
  return await run_exec(sql, (key,))
