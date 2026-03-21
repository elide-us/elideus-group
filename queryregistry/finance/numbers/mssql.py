"""MSSQL implementations for finance numbers query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "close_sequence_v1",
  "delete_v1",
  "get_by_prefix_and_account_v1",
  "get_by_scope_v1",
  "get_v1",
  "list_v1",
  "next_number_by_scope_v1",
  "next_number_v1",
  "upsert_v1",
]


def _derive_max_number(display_format: str | None) -> int:
  """Derive max number from the trailing numeric segment of a display format."""
  if not display_format:
    return 999999
  runs = [segment for segment in display_format.split("#") if segment == ""]
  if not runs:
    hash_count = display_format.count("#")
    return 10 ** hash_count - 1 if hash_count > 0 else 999999
  trailing_hashes = 0
  for char in reversed(display_format):
    if char == "#":
      trailing_hashes += 1
    elif trailing_hashes > 0:
      break
  if trailing_hashes <= 0:
    hash_count = display_format.count("#")
    return 10 ** hash_count - 1 if hash_count > 0 else 999999
  return 10 ** trailing_hashes - 1


_LIST_SELECT = """
    SELECT
      number.recid,
      number.accounts_guid,
      number.element_prefix,
      number.element_account_number,
      number.element_last_number,
      number.element_allocation_size,
      number.element_reset_policy,
      number.element_pattern,
      number.element_display_format,
      number.element_max_number,
      number.element_sequence_status,
      number.element_sequence_type,
      number.element_series_number,
      number.element_scope,
      (number.element_max_number - number.element_last_number) AS remaining,
      number.element_created_on,
      number.element_modified_on,
      account.element_name AS account_name
    FROM finance_numbers AS number
    LEFT JOIN finance_accounts AS account
      ON account.element_guid = number.accounts_guid
"""


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = f"""
{_LIST_SELECT}
    ORDER BY number.element_prefix, number.element_scope, number.element_series_number DESC, number.recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def get_by_prefix_and_account_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_LIST_SELECT}
    WHERE number.element_prefix = ?
      AND number.element_account_number = ?
    ORDER BY number.element_series_number DESC, number.recid DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["prefix"], args["account_number"]))


async def get_by_scope_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_LIST_SELECT}
    WHERE number.element_prefix = ?
      AND number.element_scope = ?
      AND number.element_sequence_status = 1
    ORDER BY number.element_series_number DESC, number.recid DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["prefix"], args["scope"]))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_LIST_SELECT}
    WHERE number.recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  max_number = args.get("max_number")
  if max_number is None:
    max_number = _derive_max_number(args.get("display_format"))

  sql = """
    SET NOCOUNT ON;
    DECLARE @result TABLE (
      recid BIGINT,
      accounts_guid UNIQUEIDENTIFIER,
      element_prefix NVARCHAR(10),
      element_account_number NVARCHAR(10),
      element_last_number BIGINT,
      element_max_number BIGINT,
      element_allocation_size INT,
      element_reset_policy NVARCHAR(20),
      element_sequence_status TINYINT,
      element_sequence_type NVARCHAR(20),
      element_series_number INT,
      element_scope NVARCHAR(64),
      element_pattern NVARCHAR(256),
      element_display_format NVARCHAR(256),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    MERGE finance_numbers AS target
    USING (
      SELECT
        ? AS recid,
        TRY_CAST(? AS UNIQUEIDENTIFIER) AS accounts_guid,
        ? AS element_prefix,
        ? AS element_account_number,
        ? AS element_last_number,
        ? AS element_max_number,
        ? AS element_allocation_size,
        ? AS element_reset_policy,
        ? AS element_sequence_status,
        ? AS element_sequence_type,
        ? AS element_series_number,
        ? AS element_scope,
        ? AS element_pattern,
        ? AS element_display_format
    ) AS source
    ON (
      (source.recid IS NOT NULL AND target.recid = source.recid)
      OR (
        source.recid IS NULL
        AND target.element_prefix = source.element_prefix
        AND target.element_account_number = source.element_account_number
        AND target.element_series_number = source.element_series_number
      )
    )
    WHEN MATCHED THEN
      UPDATE SET
        target.accounts_guid = source.accounts_guid,
        target.element_prefix = source.element_prefix,
        target.element_account_number = source.element_account_number,
        target.element_last_number = source.element_last_number,
        target.element_max_number = source.element_max_number,
        target.element_allocation_size = source.element_allocation_size,
        target.element_reset_policy = source.element_reset_policy,
        target.element_sequence_status = source.element_sequence_status,
        target.element_sequence_type = source.element_sequence_type,
        target.element_series_number = source.element_series_number,
        target.element_scope = source.element_scope,
        target.element_pattern = source.element_pattern,
        target.element_display_format = source.element_display_format,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        accounts_guid, element_prefix, element_account_number,
        element_last_number, element_max_number, element_allocation_size,
        element_reset_policy, element_sequence_status, element_sequence_type,
        element_series_number, element_scope, element_pattern,
        element_display_format, element_created_on, element_modified_on
      )
      VALUES (
        source.accounts_guid, source.element_prefix, source.element_account_number,
        source.element_last_number, source.element_max_number, source.element_allocation_size,
        source.element_reset_policy, source.element_sequence_status, source.element_sequence_type,
        source.element_series_number, source.element_scope, source.element_pattern,
        source.element_display_format, SYSUTCDATETIME(), SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid, inserted.accounts_guid, inserted.element_prefix,
      inserted.element_account_number, inserted.element_last_number,
      inserted.element_max_number, inserted.element_allocation_size,
      inserted.element_reset_policy, inserted.element_sequence_status,
      inserted.element_sequence_type, inserted.element_series_number,
      inserted.element_scope, inserted.element_pattern, inserted.element_display_format,
      inserted.element_created_on, inserted.element_modified_on
    INTO @result;

    SELECT *, (element_max_number - element_last_number) AS remaining
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("recid"),
    args["accounts_guid"],
    args.get("prefix"),
    args["account_number"],
    args["last_number"],
    max_number,
    args["allocation_size"],
    args["reset_policy"],
    args.get("sequence_status", 1),
    args.get("sequence_type", "continuous"),
    args.get("series_number", 1),
    args.get("scope"),
    args.get("pattern"),
    args.get("display_format"),
  )
  return await run_json_one(sql, params)


async def close_sequence_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @result TABLE (
      recid BIGINT,
      accounts_guid UNIQUEIDENTIFIER,
      element_prefix NVARCHAR(10),
      element_account_number NVARCHAR(10),
      element_last_number BIGINT,
      element_max_number BIGINT,
      element_allocation_size INT,
      element_reset_policy NVARCHAR(20),
      element_sequence_status TINYINT,
      element_sequence_type NVARCHAR(20),
      element_series_number INT,
      element_scope NVARCHAR(64),
      element_pattern NVARCHAR(256),
      element_display_format NVARCHAR(256),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE finance_numbers
    SET element_sequence_status = 0,
        element_modified_on = SYSUTCDATETIME()
    OUTPUT
      inserted.recid, inserted.accounts_guid, inserted.element_prefix,
      inserted.element_account_number, inserted.element_last_number,
      inserted.element_max_number, inserted.element_allocation_size,
      inserted.element_reset_policy, inserted.element_sequence_status,
      inserted.element_sequence_type, inserted.element_series_number,
      inserted.element_scope, inserted.element_pattern, inserted.element_display_format,
      inserted.element_created_on, inserted.element_modified_on
    INTO @result
    WHERE recid = ?
      AND element_sequence_status = 1;

    SELECT *, (element_max_number - element_last_number) AS remaining
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_numbers
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))


async def next_number_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid BIGINT,
      accounts_guid UNIQUEIDENTIFIER,
      element_prefix NVARCHAR(10),
      element_account_number NVARCHAR(10),
      element_block_start BIGINT,
      element_block_end BIGINT,
      element_max_number BIGINT,
      element_allocation_size INT,
      element_sequence_status TINYINT,
      element_sequence_type NVARCHAR(20),
      element_series_number INT,
      element_scope NVARCHAR(64),
      element_reset_policy NVARCHAR(20),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE finance_numbers WITH (UPDLOCK, HOLDLOCK)
    SET element_last_number = element_last_number + element_allocation_size,
        element_modified_on = SYSUTCDATETIME()
    OUTPUT
      inserted.recid,
      inserted.accounts_guid,
      inserted.element_prefix,
      inserted.element_account_number,
      (inserted.element_last_number - inserted.element_allocation_size + 1),
      inserted.element_last_number,
      inserted.element_max_number,
      inserted.element_allocation_size,
      inserted.element_sequence_status,
      inserted.element_sequence_type,
      inserted.element_series_number,
      inserted.element_scope,
      inserted.element_reset_policy,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result
    WHERE recid = ?
      AND element_sequence_status = 1
      AND element_last_number + element_allocation_size <= element_max_number;

    SELECT *, (element_max_number - element_block_end) AS remaining
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def next_number_by_scope_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid BIGINT,
      accounts_guid UNIQUEIDENTIFIER,
      element_prefix NVARCHAR(10),
      element_account_number NVARCHAR(10),
      element_block_start BIGINT,
      element_block_end BIGINT,
      element_max_number BIGINT,
      element_allocation_size INT,
      element_sequence_status TINYINT,
      element_sequence_type NVARCHAR(20),
      element_series_number INT,
      element_scope NVARCHAR(64),
      element_reset_policy NVARCHAR(20),
      element_pattern NVARCHAR(256),
      element_display_format NVARCHAR(256),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    ;WITH target AS (
      SELECT TOP (1) *
      FROM finance_numbers WITH (UPDLOCK, HOLDLOCK)
      WHERE element_prefix = ?
        AND element_scope = ?
        AND element_sequence_status = 1
      ORDER BY element_series_number DESC, recid DESC
    )
    UPDATE target
    SET element_last_number = element_last_number + element_allocation_size,
        element_modified_on = SYSUTCDATETIME()
    OUTPUT
      inserted.recid,
      inserted.accounts_guid,
      inserted.element_prefix,
      inserted.element_account_number,
      (inserted.element_last_number - inserted.element_allocation_size + 1),
      inserted.element_last_number,
      inserted.element_max_number,
      inserted.element_allocation_size,
      inserted.element_sequence_status,
      inserted.element_sequence_type,
      inserted.element_series_number,
      inserted.element_scope,
      inserted.element_reset_policy,
      inserted.element_pattern,
      inserted.element_display_format,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result
    WHERE element_last_number + element_allocation_size <= element_max_number;

    SELECT *, (element_max_number - element_block_end) AS remaining
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["prefix"], args["scope"]))
