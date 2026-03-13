"""MSSQL implementations for finance periods query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = ["delete_v1", "get_v1", "list_by_year_v1", "list_v1", "upsert_v1"]


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
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
      fp.element_created_on,
      fp.element_modified_on
    FROM finance_periods fp
    LEFT JOIN finance_numbers fn ON fn.recid = fp.numbers_recid
    ORDER BY fp.element_year ASC, fp.element_period_number ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def list_by_year_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
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
      fp.element_created_on,
      fp.element_modified_on
    FROM finance_periods fp
    LEFT JOIN finance_numbers fn ON fn.recid = fp.numbers_recid
    WHERE fp.element_year = ?
    ORDER BY fp.element_period_number ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["year"],))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
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
      fp.element_created_on,
      fp.element_modified_on
    FROM finance_periods fp
    LEFT JOIN finance_numbers fn ON fn.recid = fp.numbers_recid
    WHERE fp.element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"],))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
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
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (args["guid"],))
