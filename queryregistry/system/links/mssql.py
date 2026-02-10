"""MSSQL implementations for system links query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_json_many

from queryregistry.models import DBResponse

__all__ = [
  "get_home_links",
  "get_navbar_routes",
]


def _normalize_payload(rows: list[Any]) -> list[dict[str, Any]]:
  return [dict(row) for row in rows]


async def get_home_links(args: Mapping[str, Any]) -> DBResponse:
  role_mask = int(args.get("role_mask", 0) or 0)
  sql = """
    SELECT
      element_title AS title,
      element_url AS url,
      element_url AS path,
      element_title AS name,
      CAST(NULL AS nvarchar(256)) AS icon,
      element_sequence AS sequence
    FROM (
      SELECT
        element_title,
        element_url,
        element_sequence,
        0 AS element_roles
      FROM frontend_links
    ) AS links
    WHERE element_roles = 0 OR (element_roles & ?) = element_roles
    ORDER BY element_sequence
    FOR JSON PATH;
  """
  response = await run_json_many(sql, (role_mask,))
  return DBResponse(payload=_normalize_payload(response.rows))


async def get_navbar_routes(args: Mapping[str, Any]) -> DBResponse:
  role_mask = int(args.get("role_mask", 0) or 0)
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
  response = await run_json_many(sql, (role_mask,))
  return DBResponse(payload=_normalize_payload(response.rows))
