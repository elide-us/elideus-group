"""MSSQL implementations for system public query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_exec, run_json_many

from queryregistry.models import DBResponse

__all__ = [
  "delete_route_v1",
  "get_home_links",
  "get_navbar_routes",
  "get_routes_v1",
  "upsert_route_v1",
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


async def get_routes_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      element_path,
      element_name,
      element_icon,
      element_sequence,
      element_roles
    FROM frontend_routes
    ORDER BY element_sequence
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def upsert_route_v1(args: Mapping[str, Any]) -> DBResponse:
  path = args["path"]
  name = args["name"]
  icon = args.get("icon")
  sequence = int(args["sequence"])
  roles = int(args["roles"])
  response = await run_exec(
    "UPDATE frontend_routes SET element_name = ?, element_icon = ?, element_sequence = ?, element_roles = ? WHERE element_path = ?;",
    (name, icon, sequence, roles, path),
  )
  if response.rowcount == 0:
    response = await run_exec(
      "INSERT INTO frontend_routes (element_path, element_name, element_icon, element_sequence, element_roles) VALUES (?, ?, ?, ?, ?);",
      (path, name, icon, sequence, roles),
    )
  return response


async def delete_route_v1(args: Mapping[str, Any]) -> DBResponse:
  path = args["path"]
  sql = "DELETE FROM frontend_routes WHERE element_path = ?;"
  return await run_exec(sql, (path,))
