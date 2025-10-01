"""Public config variable queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "get_hostname_v1",
  "get_repo_v1",
  "get_version_v1",
]


def get_hostname_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT element_value AS hostname
    FROM system_config
    WHERE element_key = 'hostname'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(DbRunMode.JSON_ONE, sql, ())


def get_version_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT element_value AS version
    FROM system_config
    WHERE element_key = 'version'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(DbRunMode.JSON_ONE, sql, ())


def get_repo_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT element_value AS repo
    FROM system_config
    WHERE element_key = 'repo'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(DbRunMode.JSON_ONE, sql, ())
