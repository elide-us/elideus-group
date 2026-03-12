"""MSSQL implementations for system models query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from queryregistry.models import DBResponse

__all__ = [
  "delete_v1",
  "get_by_name_v1",
  "list_v1",
  "upsert_v1",
]


async def list_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_api_provider,
      element_is_active
    FROM assistant_models
    ORDER BY element_name
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def get_by_name_v1(args: Mapping[str, Any]) -> DBResponse:
  name = args["name"]
  sql = """
    SELECT recid
    FROM assistant_models
    WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (name,))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args.get("recid")
  name = args["name"]
  api_provider = args.get("api_provider", "openai")
  is_active = bool(args.get("is_active", True))

  if recid is not None:
    rc = await run_exec(
      """
        UPDATE assistant_models
        SET element_name = ?,
            element_api_provider = ?,
            element_is_active = ?,
            element_modified_on = SYSUTCDATETIME()
        WHERE recid = ?;
      """,
      (name, api_provider, is_active, recid),
    )
    if rc.rowcount:
      return rc

  rc = await run_exec(
    """
      UPDATE assistant_models
      SET element_api_provider = ?,
          element_is_active = ?,
          element_modified_on = SYSUTCDATETIME()
      WHERE element_name = ?;
    """,
    (api_provider, is_active, name),
  )
  if rc.rowcount:
    return rc

  return await run_exec(
    """
      INSERT INTO assistant_models (
        element_name, element_api_provider, element_is_active
      ) VALUES (?, ?, ?);
    """,
    (name, api_provider, is_active),
  )


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args.get("recid")
  name = args.get("name")
  if recid is not None:
    return await run_exec("DELETE FROM assistant_models WHERE recid = ?;", (recid,))
  if name is not None:
    return await run_exec("DELETE FROM assistant_models WHERE element_name = ?;", (name,))
  raise ValueError("Missing identifier for model delete")
