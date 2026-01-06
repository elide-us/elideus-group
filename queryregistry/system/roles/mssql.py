"""MSSQL implementations for system roles query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from server.registry.providers.mssql import run_exec, run_json_many

from queryregistry.models import DBResponse

__all__ = [
  "delete_role",
  "list_roles",
  "upsert_role",
]


def _normalize_payload(rows: list[Any]) -> list[dict[str, Any]]:
  return [dict(row) for row in rows]


async def list_roles(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT element_name AS name, element_mask AS mask, element_display AS display
    FROM system_roles
    ORDER BY element_mask
    FOR JSON PATH;
  """
  response = await run_json_many(sql)
  return DBResponse(payload=_normalize_payload(response.rows))


async def upsert_role(args: Mapping[str, Any]) -> DBResponse:
  name = args["name"]
  mask = int(args["mask"])
  display = args.get("display")
  response = await run_exec(
    "UPDATE system_roles SET element_mask = ?, element_display = ? WHERE element_name = ?;",
    (mask, display, name),
  )
  if response.rowcount == 0:
    response = await run_exec(
      "INSERT INTO system_roles (element_name, element_mask, element_display) VALUES (?, ?, ?);",
      (name, mask, display),
    )
  return DBResponse(payload={"rowcount": response.rowcount})


async def delete_role(args: Mapping[str, Any]) -> DBResponse:
  name = args["name"]
  sql = """
    DECLARE @mask BIGINT;
    SELECT @mask = element_mask FROM system_roles WHERE element_name = ?;
    UPDATE users_roles SET element_roles = element_roles & ~@mask;
    DELETE FROM system_roles WHERE element_name = ?;
  """
  response = await run_exec(sql, (name, name))
  return DBResponse(payload={"rowcount": response.rowcount})
