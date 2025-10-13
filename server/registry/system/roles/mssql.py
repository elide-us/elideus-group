"""System role metadata queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_exec, run_json_many
from server.registry.types import DBResponse

__all__ = [
  "add_role_member_v1",
  "delete_role_v1",
  "get_role_members_v1",
  "get_role_non_members_v1",
  "list_roles_v1",
  "remove_role_member_v1",
  "upsert_role_v1",
]


async def list_roles_v1(_: dict[str, Any]) -> DBResponse:
  sql = """
    SELECT element_name AS name, element_mask AS mask, element_display AS display
    FROM system_roles
    ORDER BY element_mask
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def get_role_members_v1(args: dict[str, Any]) -> DBResponse:
  role = args["role"]
  sql = """
    SELECT au.element_guid AS guid, au.element_display AS display_name
    FROM account_users au
    JOIN users_roles ur ON au.element_guid = ur.users_guid
    JOIN system_roles sr ON sr.element_name = ?
    WHERE (ur.element_roles & sr.element_mask) > 0
    ORDER BY au.element_display
    FOR JSON PATH;
  """
  return await run_json_many(sql, (role,))


async def get_role_non_members_v1(args: dict[str, Any]) -> DBResponse:
  role = args["role"]
  sql = """
    SELECT au.element_guid AS guid, au.element_display AS display_name
    FROM account_users au
    LEFT JOIN users_roles ur ON au.element_guid = ur.users_guid
    JOIN system_roles sr ON sr.element_name = ?
    WHERE (ISNULL(ur.element_roles, 0) & sr.element_mask) = 0
    ORDER BY au.element_display
    FOR JSON PATH;
  """
  return await run_json_many(sql, (role,))


async def add_role_member_v1(args: dict[str, Any]) -> DBResponse:
  role = args["role"]
  user_guid = args["user_guid"]
  sql = """
    MERGE users_roles AS ur
    USING (SELECT ? AS users_guid, element_mask FROM system_roles WHERE element_name = ?) AS src
    ON ur.users_guid = src.users_guid
    WHEN MATCHED THEN UPDATE SET element_roles = ur.element_roles | src.element_mask
    WHEN NOT MATCHED THEN INSERT (users_guid, element_roles) VALUES (src.users_guid, src.element_mask);
  """
  return await run_exec(sql, (user_guid, role))


async def remove_role_member_v1(args: dict[str, Any]) -> DBResponse:
  role = args["role"]
  user_guid = args["user_guid"]
  sql = """
    DECLARE @mask BIGINT;
    SELECT @mask = element_mask FROM system_roles WHERE element_name = ?;
    UPDATE users_roles SET element_roles = element_roles & ~@mask WHERE users_guid = ?;
    DELETE FROM users_roles WHERE users_guid = ? AND element_roles = 0;
  """
  return await run_exec(sql, (role, user_guid, user_guid))


async def upsert_role_v1(args: dict[str, Any]) -> DBResponse:
  name = args["name"]
  mask = int(args["mask"])
  display = args.get("display")
  rc = await run_exec(
    "UPDATE system_roles SET element_mask = ?, element_display = ? WHERE element_name = ?;",
    (mask, display, name),
  )
  if rc.rowcount == 0:
    rc = await run_exec(
      "INSERT INTO system_roles (element_name, element_mask, element_display) VALUES (?, ?, ?);",
      (name, mask, display),
    )
  return rc


async def delete_role_v1(args: dict[str, Any]) -> DBResponse:
  name = args["name"]
  sql = """
    DECLARE @mask BIGINT;
    SELECT @mask = element_mask FROM system_roles WHERE element_name = ?;
    UPDATE users_roles SET element_roles = element_roles & ~@mask;
    DELETE FROM system_roles WHERE element_name = ?;
  """
  return await run_exec(sql, (name, name))
