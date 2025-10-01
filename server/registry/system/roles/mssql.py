"""System role metadata queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "list_roles_v1",
]


def list_roles_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT element_name AS name, element_mask AS mask, element_display AS display
    FROM system_roles
    ORDER BY element_mask
    FOR JSON PATH;
  """
  return Operation(DbRunMode.JSON_MANY, sql, ())
