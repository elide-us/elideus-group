"""MSSQL helpers for service page registry operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.registry.providers.mssql import run_exec, run_json_many, run_json_one
from server.registry.types import DBResponse

__all__ = [
  "create_v1",
  "delete_v1",
  "get_by_route_v1",
  "get_v1",
  "list_v1",
  "update_v1",
]


def _to_bool_flag(value: Any) -> int:
  return 1 if bool(value) else 0


async def list_v1(params: dict[str, Any]) -> DBResponse:
  filters: list[str] = []
  args: list[Any] = []

  if "element_is_active" in params:
    filters.append("sp.element_is_active = ?")
    args.append(_to_bool_flag(params["element_is_active"]))

  where_clause = ""
  if filters:
    where_clause = "WHERE " + " AND ".join(filters)

  sql = f"""
    SELECT
      sp.recid,
      sp.element_route_name,
      sp.element_pageblob,
      sp.element_version,
      sp.element_created_on,
      sp.element_modified_on,
      sp.element_created_by,
      sp.element_modified_by,
      sp.element_is_active
    FROM service_pages sp
    {where_clause}
    ORDER BY sp.element_route_name, sp.element_version DESC
    FOR JSON PATH;
  """
  return await run_json_many(sql, tuple(args))


async def get_v1(params: dict[str, Any]) -> DBResponse:
  recid = int(params["recid"])
  sql = """
    SELECT
      sp.recid,
      sp.element_route_name,
      sp.element_pageblob,
      sp.element_version,
      sp.element_created_on,
      sp.element_modified_on,
      sp.element_created_by,
      sp.element_modified_by,
      sp.element_is_active
    FROM service_pages sp
    WHERE sp.recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (recid,))


async def get_by_route_v1(params: dict[str, Any]) -> DBResponse:
  route_name = str(params["element_route_name"])
  filters = ["sp.element_route_name = ?"]
  args: list[Any] = [route_name]

  if "element_is_active" in params:
    filters.append("sp.element_is_active = ?")
    args.append(_to_bool_flag(params["element_is_active"]))

  where_clause = " AND ".join(filters)
  sql = f"""
    SELECT TOP 1
      sp.recid,
      sp.element_route_name,
      sp.element_pageblob,
      sp.element_version,
      sp.element_created_on,
      sp.element_modified_on,
      sp.element_created_by,
      sp.element_modified_by,
      sp.element_is_active
    FROM service_pages sp
    WHERE {where_clause}
    ORDER BY sp.element_version DESC, sp.element_modified_on DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, tuple(args))


async def create_v1(params: dict[str, Any]) -> DBResponse:
  recid = int(params["recid"])
  route_name = str(params["element_route_name"])
  page_blob = str(params["element_pageblob"])
  version = int(params.get("element_version", 1))
  created_by = str(UUID(str(params["element_created_by"])))
  modified_by = str(UUID(str(params["element_modified_by"])))
  is_active = _to_bool_flag(params.get("element_is_active", True))
  sql = """
    INSERT INTO service_pages (
      recid,
      element_route_name,
      element_pageblob,
      element_version,
      element_created_by,
      element_modified_by,
      element_is_active
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
  """
  return await run_exec(
    sql,
    (recid, route_name, page_blob, version, created_by, modified_by, is_active),
  )


async def update_v1(params: dict[str, Any]) -> DBResponse:
  recid = int(params["recid"])
  modified_by = str(UUID(str(params["element_modified_by"])))

  assignments: list[str] = ["element_modified_by = ?", "element_modified_on = SYSUTCDATETIME()"]
  args: list[Any] = [modified_by]

  if "element_route_name" in params:
    assignments.append("element_route_name = ?")
    args.append(str(params["element_route_name"]))
  if "element_pageblob" in params:
    assignments.append("element_pageblob = ?")
    args.append(str(params["element_pageblob"]))
  if "element_version" in params:
    assignments.append("element_version = ?")
    args.append(int(params["element_version"]))
  if "element_is_active" in params:
    assignments.append("element_is_active = ?")
    args.append(_to_bool_flag(params["element_is_active"]))

  sql = f"""
    UPDATE service_pages
    SET {", ".join(assignments)}
    WHERE recid = ?;
  """
  args.append(recid)
  return await run_exec(sql, tuple(args))


async def delete_v1(params: dict[str, Any]) -> DBResponse:
  recid = int(params["recid"])
  sql = "DELETE FROM service_pages WHERE recid = ?;"
  return await run_exec(sql, (recid,))
