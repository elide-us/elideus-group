"""MSSQL implementations for finance periods query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one
from server.modules.models.finance_statuses import PERIOD_CLOSED, PERIOD_LOCKED, PERIOD_OPEN

__all__ = [
  "close_period_v1",
  "delete_v1",
  "get_v1",
  "list_by_year_v1",
  "list_close_blockers_v1",
  "list_v1",
  "lock_period_v1",
  "reopen_period_v1",
  "unlock_period_v1",
  "upsert_v1",
]

_PERIOD_SELECT = """
    SELECT
      fp.element_guid,
      fp.element_year,
      fp.element_period_number,
      fp.element_period_name,
      fp.element_start_date,
      fp.element_end_date,
      fp.element_days_in_period,
      fp.element_quarter_number,
      fp.element_has_closing_week,
      fp.element_is_leap_adjustment,
      fp.element_anchor_event,
      fp.element_close_type,
      fp.element_status,
      fp.numbers_recid,
      fn.element_display_format,
      fp.element_closed_by,
      fp.element_closed_on,
      fp.element_locked_by,
      fp.element_locked_on,
      fp.element_created_on,
      fp.element_modified_on
    FROM finance_periods fp
    LEFT JOIN finance_numbers fn ON fn.recid = fp.numbers_recid
"""


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = f"""
{_PERIOD_SELECT}
    ORDER BY fp.element_year ASC, fp.element_period_number ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def list_by_year_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_PERIOD_SELECT}
    WHERE fp.element_year = ?
    ORDER BY fp.element_period_number ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["year"],))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_PERIOD_SELECT}
    WHERE fp.element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"],))


async def close_period_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;

    UPDATE finance_periods
    SET
      element_status = {PERIOD_CLOSED},
      element_closed_by = ?,
      element_closed_on = SYSUTCDATETIME(),
      element_modified_on = SYSUTCDATETIME()
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND element_status = {PERIOD_OPEN};

{_PERIOD_SELECT}
    WHERE fp.element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND fp.element_status = {PERIOD_CLOSED}
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["closed_by"], args["guid"], args["guid"]))


async def reopen_period_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;

    UPDATE finance_periods
    SET
      element_status = {PERIOD_OPEN},
      element_closed_by = NULL,
      element_closed_on = NULL,
      element_modified_on = SYSUTCDATETIME()
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND element_status = {PERIOD_CLOSED};

{_PERIOD_SELECT}
    WHERE fp.element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND fp.element_status = {PERIOD_OPEN}
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"], args["guid"]))


async def lock_period_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;

    UPDATE finance_periods
    SET
      element_status = {PERIOD_LOCKED},
      element_locked_by = ?,
      element_locked_on = SYSUTCDATETIME(),
      element_modified_on = SYSUTCDATETIME()
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND element_status = {PERIOD_CLOSED};

{_PERIOD_SELECT}
    WHERE fp.element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND fp.element_status = {PERIOD_LOCKED}
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["locked_by"], args["guid"], args["guid"]))


async def unlock_period_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
    SET NOCOUNT ON;

    UPDATE finance_periods
    SET
      element_status = {PERIOD_CLOSED},
      element_locked_by = NULL,
      element_locked_on = NULL,
      element_modified_on = SYSUTCDATETIME()
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND element_status = {PERIOD_LOCKED};

{_PERIOD_SELECT}
    WHERE fp.element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND fp.element_status = {PERIOD_CLOSED}
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"], args["guid"]))


async def list_close_blockers_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      period_guid,
      blocker_type,
      blocker_recid,
      blocker_name,
      blocker_reason
    FROM vw_finance_period_close_blockers
    WHERE period_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    ORDER BY blocker_type, blocker_recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["period_guid"],))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      element_guid uniqueidentifier,
      element_year int,
      element_period_number tinyint,
      element_period_name nvarchar(50),
      element_start_date date,
      element_end_date date,
      element_days_in_period tinyint,
      element_quarter_number tinyint,
      element_has_closing_week bit,
      element_is_leap_adjustment bit,
      element_anchor_event nvarchar(50),
      element_close_type tinyint,
      element_status tinyint,
      numbers_recid bigint,
      element_created_on datetimeoffset,
      element_modified_on datetimeoffset
    );

    MERGE finance_periods AS target
    USING (
      SELECT
        COALESCE(TRY_CAST(? AS UNIQUEIDENTIFIER), NEWID()) AS element_guid,
        ? AS element_year,
        ? AS element_period_number,
        ? AS element_period_name,
        TRY_CAST(? AS DATE) AS element_start_date,
        TRY_CAST(? AS DATE) AS element_end_date,
        ? AS element_days_in_period,
        ? AS element_quarter_number,
        ? AS element_has_closing_week,
        ? AS element_is_leap_adjustment,
        ? AS element_anchor_event,
        ? AS element_close_type,
        ? AS element_status,
        ? AS numbers_recid
    ) AS source
    ON target.element_year = source.element_year
      AND target.element_period_number = source.element_period_number
    WHEN MATCHED THEN
      UPDATE SET
        target.element_period_name = source.element_period_name,
        target.element_start_date = source.element_start_date,
        target.element_end_date = source.element_end_date,
        target.element_days_in_period = source.element_days_in_period,
        target.element_quarter_number = source.element_quarter_number,
        target.element_has_closing_week = source.element_has_closing_week,
        target.element_is_leap_adjustment = source.element_is_leap_adjustment,
        target.element_anchor_event = source.element_anchor_event,
        target.element_close_type = source.element_close_type,
        target.element_status = source.element_status,
        target.numbers_recid = source.numbers_recid,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_guid,
        element_year,
        element_period_number,
        element_period_name,
        element_start_date,
        element_end_date,
        element_days_in_period,
        element_quarter_number,
        element_has_closing_week,
        element_is_leap_adjustment,
        element_anchor_event,
        element_close_type,
        element_status,
        numbers_recid,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_guid,
        source.element_year,
        source.element_period_number,
        source.element_period_name,
        source.element_start_date,
        source.element_end_date,
        source.element_days_in_period,
        source.element_quarter_number,
        source.element_has_closing_week,
        source.element_is_leap_adjustment,
        source.element_anchor_event,
        source.element_close_type,
        source.element_status,
        source.numbers_recid,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.element_guid,
      inserted.element_year,
      inserted.element_period_number,
      inserted.element_period_name,
      inserted.element_start_date,
      inserted.element_end_date,
      inserted.element_days_in_period,
      inserted.element_quarter_number,
      inserted.element_has_closing_week,
      inserted.element_is_leap_adjustment,
      inserted.element_anchor_event,
      inserted.element_close_type,
      inserted.element_status,
      inserted.numbers_recid,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result;

    SELECT * FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("guid"),
    args["year"],
    args["period_number"],
    args["period_name"],
    args["start_date"],
    args["end_date"],
    args["days_in_period"],
    args["quarter_number"],
    args["has_closing_week"],
    args["is_leap_adjustment"],
    args.get("anchor_event"),
    args["close_type"],
    args["status"],
    args.get("numbers_recid"),
  )
  return await run_json_one(sql, params)


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_periods
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
  """
  return await run_exec(sql, (args["guid"],))
