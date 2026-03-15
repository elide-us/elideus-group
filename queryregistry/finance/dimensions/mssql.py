"""MSSQL implementations for finance dimensions query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = ["delete_v1", "get_v1", "list_by_name_v1", "list_v1", "upsert_v1"]


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
    SELECT
      recid,
      element_name,
      element_value,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_dimensions
    ORDER BY element_name, element_value
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def list_by_name_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_value,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_dimensions
    WHERE element_name = ?
    ORDER BY element_value
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["name"],))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_value,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_dimensions
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    MERGE finance_dimensions AS target
    USING (
      SELECT
        ? AS recid,
        ? AS element_name,
        ? AS element_value,
        ? AS element_description,
        ? AS element_status
    ) AS source
    ON (
      (source.recid IS NOT NULL AND target.recid = source.recid)
      OR (source.recid IS NULL AND target.element_name = source.element_name
          AND target.element_value = source.element_value)
    )
    WHEN MATCHED THEN
      UPDATE SET
        target.element_name = source.element_name,
        target.element_value = source.element_value,
        target.element_description = source.element_description,
        target.element_status = source.element_status,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_name,
        element_value,
        element_description,
        element_status,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_name,
        source.element_value,
        source.element_description,
        source.element_status,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid,
      inserted.element_name,
      inserted.element_value,
      inserted.element_description,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("recid"),
    args["name"],
    args["value"],
    args.get("description"),
    args["status"],
  )
  return await run_json_one(sql, params)


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_dimensions
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))
