"""MSSQL implementations for finance ledgers query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from server.modules.models.finance_statuses import ELEMENT_INACTIVE
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "create_v1",
  "delete_v1",
  "get_by_name_v1",
  "get_v1",
  "journal_reference_count_v1",
  "list_v1",
  "update_v1",
]


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
    SELECT
      recid,
      element_name,
      element_description,
      element_chart_of_accounts_guid,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_ledgers
    ORDER BY element_name ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_description,
      element_chart_of_accounts_guid,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_ledgers
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def get_by_name_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_description,
      element_chart_of_accounts_guid,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_ledgers
    WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_name"],))


async def create_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid bigint,
      element_name nvarchar(200),
      element_description nvarchar(max),
      element_chart_of_accounts_guid uniqueidentifier,
      element_status tinyint,
      element_created_on datetimeoffset,
      element_modified_on datetimeoffset
    );

    INSERT INTO finance_ledgers (
      element_name,
      element_description,
      element_chart_of_accounts_guid,
      element_status,
      element_created_on,
      element_modified_on
    )
    OUTPUT
      inserted.recid,
      inserted.element_name,
      inserted.element_description,
      inserted.element_chart_of_accounts_guid,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result
    VALUES (?, ?, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, SYSUTCDATETIME(), SYSUTCDATETIME());

    SELECT * FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["element_name"],
    args.get("element_description"),
    args.get("element_chart_of_accounts_guid"),
    args["element_status"],
  )
  return await run_json_one(sql, params)


async def update_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid bigint,
      element_name nvarchar(200),
      element_description nvarchar(max),
      element_chart_of_accounts_guid uniqueidentifier,
      element_status tinyint,
      element_created_on datetimeoffset,
      element_modified_on datetimeoffset
    );

    UPDATE finance_ledgers
    SET
      element_name = ?,
      element_description = ?,
      element_chart_of_accounts_guid = TRY_CAST(? AS UNIQUEIDENTIFIER),
      element_status = ?,
      element_modified_on = SYSUTCDATETIME()
    OUTPUT
      inserted.recid,
      inserted.element_name,
      inserted.element_description,
      inserted.element_chart_of_accounts_guid,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result
    WHERE recid = ?;

    SELECT * FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["element_name"],
    args.get("element_description"),
    args.get("element_chart_of_accounts_guid"),
    args["element_status"],
    args["recid"],
  )
  return await run_json_one(sql, params)


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;
    UPDATE finance_ledgers
    SET
      element_status = {ELEMENT_INACTIVE},
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))


async def journal_reference_count_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT COUNT_BIG(*) AS journal_count
    FROM finance_journals
    WHERE ledgers_recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))
