"""MSSQL helpers for user action log operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.registry.providers.mssql import run_exec, run_json_many
from server.registry.types import DBResponse

__all__ = [
  "list_by_user_v1",
  "log_v1",
  "update_v1",
]


async def list_by_user_v1(params: dict[str, Any]) -> DBResponse:
  guid = str(UUID(str(params["users_guid"])))
  filters = ["ual.users_guid = ?"]
  args: list[Any] = [guid]

  action_recid = params.get("action_recid")
  if action_recid is not None:
    filters.append("ual.action_recid = ?")
    args.append(int(action_recid))

  where_clause = " AND ".join(filters)
  order_clause = "ORDER BY ual.element_logged_on DESC"
  fetch_clause = ""

  limit = params.get("limit")
  if limit is not None:
    limit_value = int(limit)
    if limit_value > 0:
      fetch_clause = " OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY"
      args.append(limit_value)

  sql = f"""
    SELECT
      ual.recid,
      ual.users_guid,
      ual.action_recid,
      aa.action_label,
      aa.action_description,
      ual.element_url,
      ual.element_logged_on,
      ual.element_notes
    FROM users_actions_log ual
    LEFT JOIN account_actions aa ON aa.recid = ual.action_recid
    WHERE {where_clause}
    {order_clause}{fetch_clause}
    FOR JSON PATH;
  """
  return await run_json_many(sql, tuple(args))


async def log_v1(params: dict[str, Any]) -> DBResponse:
  recid = int(params["recid"])
  guid = str(UUID(str(params["users_guid"])))
  action_recid = int(params["action_recid"])
  element_url = params.get("element_url")
  element_notes = params.get("element_notes")
  sql = """
    INSERT INTO users_actions_log (
      recid,
      users_guid,
      action_recid,
      element_url,
      element_notes
    ) VALUES (?, ?, ?, ?, ?);
  """
  return await run_exec(sql, (recid, guid, action_recid, element_url, element_notes))


async def update_v1(params: dict[str, Any]) -> DBResponse:
  recid = int(params["recid"])
  assignments: list[str] = []
  args: list[Any] = []

  if "element_url" in params:
    assignments.append("element_url = ?")
    args.append(params.get("element_url"))
  if "element_notes" in params:
    assignments.append("element_notes = ?")
    args.append(params.get("element_notes"))

  if not assignments:
    return DBResponse()

  args.append(recid)
  sql = f"""
    UPDATE users_actions_log
    SET {", ".join(assignments)}
    WHERE recid = ?;
  """
  return await run_exec(sql, tuple(args))
