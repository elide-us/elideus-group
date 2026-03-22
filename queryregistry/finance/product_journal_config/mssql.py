"""MSSQL implementations for finance product journal config query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = ["activate_v1", "approve_v1", "close_v1", "get_active_v1", "get_v1", "list_v1", "upsert_v1"]

_CONFIG_SELECT = """
    SELECT
      recid,
      element_category,
      element_journal_scope,
      journals_recid,
      periods_guid,
      element_approved_by,
      element_approved_on,
      element_activated_by,
      element_activated_on,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_product_journal_config
"""


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_CONFIG_SELECT}
    WHERE (? IS NULL OR element_category = ?)
      AND (? IS NULL OR periods_guid = TRY_CAST(? AS UNIQUEIDENTIFIER))
      AND (? IS NULL OR element_status = ?)
    ORDER BY periods_guid DESC, element_category ASC, recid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  category = args.get("category")
  periods_guid = args.get("periods_guid")
  status = args.get("status")
  return await run_json_many(sql, (category, category, periods_guid, periods_guid, status, status))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_CONFIG_SELECT}
    WHERE recid = TRY_CAST(? AS BIGINT)
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def get_active_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_CONFIG_SELECT}
    WHERE element_category = ?
      AND periods_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND element_status = 2
    ORDER BY recid DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["category"], args["periods_guid"]))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @result TABLE (
      recid BIGINT,
      element_category NVARCHAR(64),
      element_journal_scope NVARCHAR(64),
      journals_recid BIGINT,
      periods_guid UNIQUEIDENTIFIER,
      element_approved_by NVARCHAR(128),
      element_approved_on DATETIMEOFFSET(7),
      element_activated_by NVARCHAR(128),
      element_activated_on DATETIMEOFFSET(7),
      element_status TINYINT,
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    MERGE finance_product_journal_config AS target
    USING (
      SELECT
        TRY_CAST(? AS BIGINT) AS recid,
        ? AS element_category,
        ? AS element_journal_scope,
        TRY_CAST(? AS BIGINT) AS journals_recid,
        TRY_CAST(? AS UNIQUEIDENTIFIER) AS periods_guid,
        ? AS element_status
    ) AS source
    ON source.recid IS NOT NULL AND target.recid = source.recid
    WHEN MATCHED THEN
      UPDATE SET
        target.element_category = source.element_category,
        target.element_journal_scope = source.element_journal_scope,
        target.journals_recid = source.journals_recid,
        target.periods_guid = source.periods_guid,
        target.element_status = source.element_status,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_category,
        element_journal_scope,
        journals_recid,
        periods_guid,
        element_status,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_category,
        source.element_journal_scope,
        source.journals_recid,
        source.periods_guid,
        source.element_status,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid,
      inserted.element_category,
      inserted.element_journal_scope,
      inserted.journals_recid,
      inserted.periods_guid,
      inserted.element_approved_by,
      inserted.element_approved_on,
      inserted.element_activated_by,
      inserted.element_activated_on,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result;

    SELECT *
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("recid"),
    args["category"],
    args["journal_scope"],
    args["journals_recid"],
    args["periods_guid"],
    args["status"],
  )
  return await run_json_one(sql, params)


async def approve_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;

    UPDATE finance_product_journal_config
    SET
      element_status = 1,
      element_approved_by = ?,
      element_approved_on = SYSUTCDATETIME(),
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?
      AND element_status = 0;

{_CONFIG_SELECT}
    WHERE recid = ?
      AND element_status = 1
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["approved_by"], args["recid"], args["recid"]))


async def activate_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;

    UPDATE finance_product_journal_config
    SET
      element_status = 2,
      element_activated_by = ?,
      element_activated_on = SYSUTCDATETIME(),
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?
      AND element_status = 1;

{_CONFIG_SELECT}
    WHERE recid = ?
      AND element_status = 2
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["activated_by"], args["recid"], args["recid"]))


async def close_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;

    UPDATE finance_product_journal_config
    SET
      element_status = 3,
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?
      AND element_status = 2;

{_CONFIG_SELECT}
    WHERE recid = ?
      AND element_status = 3
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"], args["recid"]))
