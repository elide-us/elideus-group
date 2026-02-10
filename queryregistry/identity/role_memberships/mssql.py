"""MSSQL implementations for identity role memberships query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many

__all__ = [
  "add_role_member",
  "list_role_members",
  "list_role_non_members",
  "remove_role_member",
]


async def list_role_members(args: Mapping[str, Any]) -> DBResponse:
  rows = await _get_role_members(args["role"])
  return DBResponse(payload=rows)


async def list_role_non_members(args: Mapping[str, Any]) -> DBResponse:
  rows = await _get_role_non_members(args["role"])
  return DBResponse(payload=rows)


async def add_role_member(args: Mapping[str, Any]) -> DBResponse:
  rowcount = await _add_role_member(args["role"], args["user_guid"])
  return DBResponse(payload={"rowcount": rowcount})


async def remove_role_member(args: Mapping[str, Any]) -> DBResponse:
  rowcount = await _remove_role_member(args["role"], args["user_guid"])
  return DBResponse(payload={"rowcount": rowcount})


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
