"""Public link queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "get_home_links_v1",
  "get_navbar_routes_v1",
]


def get_home_links_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT
      element_title AS title,
      element_url AS url
    FROM frontend_links
    ORDER BY element_sequence
    FOR JSON PATH;
  """
  return Operation(DbRunMode.JSON_MANY, sql, ())


def get_navbar_routes_v1(args: dict[str, Any]) -> Operation:
  mask = int(args.get("role_mask", 0))
  sql = """
    SELECT
      element_path AS path,
      element_name AS name,
      element_icon AS icon,
      element_sequence AS sequence
    FROM frontend_routes
    WHERE element_roles = 0 OR (element_roles & ?) = element_roles
    ORDER BY element_sequence
    FOR JSON PATH;
  """
  return Operation(DbRunMode.JSON_MANY, sql, (mask,))
