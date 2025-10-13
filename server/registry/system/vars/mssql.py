"""Public config variable queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_json_one
from server.registry.types import DBResponse

__all__ = [
  "get_hostname_v1",
  "get_repo_v1",
  "get_version_v1",
]


async def get_hostname_v1(_: dict[str, Any]) -> DBResponse:
  sql = """
    SELECT element_value AS hostname
    FROM system_config
    WHERE element_key = 'hostname'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql)


async def get_version_v1(_: dict[str, Any]) -> DBResponse:
  sql = """
    SELECT element_value AS version
    FROM system_config
    WHERE element_key = 'version'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql)


async def get_repo_v1(_: dict[str, Any]) -> DBResponse:
  sql = """
    SELECT element_value AS repo
    FROM system_config
    WHERE element_key = 'repo'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql)
