"""MSSQL implementations for identity roles query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "add_role_member",
  "get_roles_v1",
  "list_all_role_memberships",
  "list_role_members",
  "list_role_non_members",
  "remove_role_member",
  "set_roles_v1",
]


async def list_role_members(args: Mapping[str, Any]) -> DBResponse:
  rows = await _get_role_members(args["role"])
  return DBResponse(payload=rows)


async def list_role_non_members(args: Mapping[str, Any]) -> DBResponse:
  rows = await _get_role_non_members(args["role"])
  return DBResponse(payload=rows)


async def list_all_role_memberships(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      sr.element_name AS name,
      sr.element_mask AS mask,
      sr.element_display AS display,
      (
        SELECT au.element_guid AS guid, au.element_display AS display_name
        FROM account_users au
        JOIN users_roles ur ON au.element_guid = ur.users_guid
        WHERE (ur.element_roles & sr.element_mask) > 0
        ORDER BY au.element_display
        FOR JSON PATH
      ) AS members,
      (
        SELECT au.element_guid AS guid, au.element_display AS display_name
        FROM account_users au
        LEFT JOIN users_roles ur ON au.element_guid = ur.users_guid
        WHERE (ISNULL(ur.element_roles, 0) & sr.element_mask) = 0
        ORDER BY au.element_display
        FOR JSON PATH
      ) AS non_members
    FROM system_roles sr
    ORDER BY sr.element_mask
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  response = await run_json_many(sql)
  return DBResponse(payload=_normalize_payload(response.rows))


async def add_role_member(args: Mapping[str, Any]) -> DBResponse:
  rowcount = await _add_role_member(args["role"], args["user_guid"])
  return DBResponse(payload={"rowcount": rowcount})


async def remove_role_member(args: Mapping[str, Any]) -> DBResponse:
  rowcount = await _remove_role_member(args["role"], args["user_guid"])
  return DBResponse(payload={"rowcount": rowcount})


async def get_roles_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  response = await run_json_one(
    "SELECT element_roles AS roles FROM users_roles WHERE users_guid = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (guid,),
  )
  return DBResponse(payload=response.payload, rowcount=response.rowcount)


async def set_roles_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  roles = int(args["roles"])
  if roles == 0:
    response = await run_exec("DELETE FROM users_roles WHERE users_guid = ?;", (guid,))
    return DBResponse(payload=response.payload, rowcount=response.rowcount)
  response = await run_exec(
    "UPDATE users_roles SET element_roles = ? WHERE users_guid = ?;",
    (roles, guid),
  )
  if response.rowcount == 0:
    response = await run_exec(
      "INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);",
      (guid, roles),
    )
  return DBResponse(payload=response.payload, rowcount=response.rowcount)


def _normalize_payload(rows: list[Any]) -> list[dict[str, Any]]:
  return [dict(row) for row in rows]


async def _get_role_members(role: str) -> list[dict[str, Any]]:
  sql = """
    SELECT au.element_guid AS guid, au.element_display AS display_name
    FROM account_users au
    JOIN users_roles ur ON au.element_guid = ur.users_guid
    JOIN system_roles sr ON sr.element_name = ?
    WHERE (ur.element_roles & sr.element_mask) > 0
    ORDER BY au.element_display
    FOR JSON PATH;
  """
  response = await run_json_many(sql, (role,))
  return _normalize_payload(response.rows)


async def _get_role_non_members(role: str) -> list[dict[str, Any]]:
  sql = """
    SELECT au.element_guid AS guid, au.element_display AS display_name
    FROM account_users au
    LEFT JOIN users_roles ur ON au.element_guid = ur.users_guid
    JOIN system_roles sr ON sr.element_name = ?
    WHERE (ISNULL(ur.element_roles, 0) & sr.element_mask) = 0
    ORDER BY au.element_display
    FOR JSON PATH;
  """
  response = await run_json_many(sql, (role,))
  return _normalize_payload(response.rows)


async def _add_role_member(role: str, user_guid: str) -> int:
  sql = """
    MERGE users_roles AS ur
    USING (SELECT ? AS users_guid, element_mask FROM system_roles WHERE element_name = ?) AS src
    ON ur.users_guid = src.users_guid
    WHEN MATCHED THEN UPDATE SET element_roles = ur.element_roles | src.element_mask
    WHEN NOT MATCHED THEN INSERT (users_guid, element_roles) VALUES (src.users_guid, src.element_mask);
  """
  response = await run_exec(sql, (user_guid, role))
  return response.rowcount


async def _remove_role_member(role: str, user_guid: str) -> int:
  sql = """
    DECLARE @mask BIGINT;
    SELECT @mask = element_mask FROM system_roles WHERE element_name = ?;
    UPDATE users_roles SET element_roles = element_roles & ~@mask WHERE users_guid = ?;
    DELETE FROM users_roles WHERE users_guid = ? AND element_roles = 0;
  """
  response = await run_exec(sql, (role, user_guid, user_guid))
  return response.rowcount
