"""MSSQL helpers for user enablement registry operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.registry.providers.mssql import run_exec, run_json_one
from server.registry.types import DBResponse

__all__ = [
  "get_by_user_v1",
  "upsert_v1",
]


async def get_by_user_v1(params: dict[str, Any]) -> DBResponse:
  guid = str(UUID(str(params["users_guid"])))
  sql = """
    SELECT TOP 1
      ue.users_guid,
      ue.element_enablements,
      ue.created_on,
      ue.modified_on
    FROM users_enablements ue
    WHERE ue.users_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (guid,))


async def upsert_v1(params: dict[str, Any]) -> DBResponse:
  guid = str(UUID(str(params["users_guid"])))
  enablements = str(params["element_enablements"])
  updated = await run_exec(
    """
    UPDATE users_enablements
    SET element_enablements = ?, modified_on = SYSUTCDATETIME()
    WHERE users_guid = ?;
    """,
    (enablements, guid),
  )
  if updated.rowcount == 0:
    return await run_exec(
      """
      INSERT INTO users_enablements (users_guid, element_enablements)
      VALUES (?, ?);
      """,
      (guid, enablements),
    )
  return updated
