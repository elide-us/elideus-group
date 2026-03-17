from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one


async def list_vendors_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
    SELECT
      recid,
      element_name,
      element_display,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_vendors
    ORDER BY element_name
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def get_vendor_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_display,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_vendors
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def get_vendor_by_name_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_display,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_vendors
    WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_name"],))


async def upsert_vendor_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    MERGE finance_vendors AS target
    USING (
      SELECT
        TRY_CAST(? AS BIGINT) AS recid,
        ? AS element_name,
        ? AS element_display,
        ? AS element_description,
        ? AS element_status
    ) AS source
    ON (source.recid IS NOT NULL AND target.recid = source.recid)
      OR (source.recid IS NULL AND target.element_name = source.element_name)
    WHEN MATCHED THEN
      UPDATE SET
        target.element_name = source.element_name,
        target.element_display = source.element_display,
        target.element_description = source.element_description,
        target.element_status = source.element_status,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_name,
        element_display,
        element_description,
        element_status,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_name,
        source.element_display,
        source.element_description,
        source.element_status,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid,
      inserted.element_name,
      inserted.element_display,
      inserted.element_description,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("recid"),
    args["element_name"],
    args.get("element_display"),
    args.get("element_description"),
    args["element_status"],
  )
  return await run_json_one(sql, params)


async def delete_vendor_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_vendors
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))
