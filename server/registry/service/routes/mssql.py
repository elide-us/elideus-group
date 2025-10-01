"""Service route management helpers for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation, exec_op, exec_query

__all__ = [
  "delete_route_v1",
  "get_routes_v1",
  "upsert_route_v1",
]


def get_routes_v1(_: dict[str, Any]) -> Operation:
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
  return Operation(DbRunMode.JSON_MANY, sql, ())


async def upsert_route_v1(args: dict[str, Any]):
  path = args["path"]
  name = args["name"]
  icon = args.get("icon")
  sequence = int(args["sequence"])
  roles = int(args["roles"])
  rc = await exec_query(exec_op(
    "UPDATE frontend_routes SET element_name = ?, element_icon = ?, element_sequence = ?, element_roles = ? WHERE element_path = ?;",
    (name, icon, sequence, roles, path),
  ))
  if rc.rowcount == 0:
    rc = await exec_query(exec_op(
      "INSERT INTO frontend_routes (element_path, element_name, element_icon, element_sequence, element_roles) VALUES (?, ?, ?, ?, ?);",
      (path, name, icon, sequence, roles),
    ))
  return rc


def delete_route_v1(args: dict[str, Any]) -> Operation:
  path = args["path"]
  sql = "DELETE FROM frontend_routes WHERE element_path = ?;"
  return Operation(DbRunMode.EXEC, sql, (path,))
