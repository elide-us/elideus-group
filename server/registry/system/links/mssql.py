"""Public link queries for MSSQL."""

from __future__ import annotations

from server.registry.providers.mssql import run_json_many
from server.registry.types import DBResponse

from .model import NavbarRoutesParams

__all__ = [
  "get_home_links_v1",
  "get_navbar_routes_v1",
]


async def get_home_links_v1(_: object) -> DBResponse:
  sql = """
    SELECT
      element_title AS title,
      element_url AS url
    FROM frontend_links
    ORDER BY element_sequence
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def get_navbar_routes_v1(args: NavbarRoutesParams) -> DBResponse:
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
  return await run_json_many(sql, (mask,))
