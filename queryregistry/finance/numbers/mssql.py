"""MSSQL implementations for finance numbers query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = ["delete_v1", "get_by_prefix_and_account_v1", "get_v1", "list_v1", "next_number_v1", "upsert_v1"]


def _derive_max_number(display_format: str | None) -> int:
  """Derive max number from display format by counting # placeholders.

  Returns 10^n - 1 where n is the count of # characters.
  Falls back to 999999 if no format or no # characters.
  """
  if not display_format:
    return 999999
  hash_count = display_format.count("#")
  if hash_count == 0:
    return 999999
  return 10 ** hash_count - 1


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
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
      (number.element_max_number - number.element_last_number) AS remaining,
      number.element_created_on,
      number.element_modified_on,
      account.element_name AS account_name
    FROM finance_numbers AS number
    LEFT JOIN finance_accounts AS account
      ON account.element_guid = number.accounts_guid
    ORDER BY number.recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def get_by_prefix_and_account_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT TOP 1
      recid,
      element_prefix,
      element_account_number,
      element_pattern,
      element_display_format,
      element_max_number,
      element_sequence_status,
      (element_max_number - element_last_number) AS remaining
    FROM finance_numbers
    WHERE element_prefix = ?
      AND element_account_number = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["prefix"], args["account_number"]))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
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
      (number.element_max_number - number.element_last_number) AS remaining,
      number.element_created_on,
      number.element_modified_on,
      account.element_name AS account_name
    FROM finance_numbers AS number
    LEFT JOIN finance_accounts AS account
      ON account.element_guid = number.accounts_guid
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
        ? AS element_pattern,
        ? AS element_display_format
    ) AS source
    ON (
      (source.recid IS NOT NULL AND target.recid = source.recid)
      OR (
        source.recid IS NULL
        AND target.element_prefix = source.element_prefix
        AND target.element_account_number = source.element_account_number
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
        target.element_pattern = source.element_pattern,
        target.element_display_format = source.element_display_format,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        accounts_guid, element_prefix, element_account_number,
        element_last_number, element_max_number, element_allocation_size,
        element_reset_policy, element_sequence_status, element_pattern,
        element_display_format, element_created_on, element_modified_on
      )
      VALUES (
        source.accounts_guid, source.element_prefix, source.element_account_number,
        source.element_last_number, source.element_max_number, source.element_allocation_size,
        source.element_reset_policy, source.element_sequence_status, source.element_pattern,
        source.element_display_format, SYSUTCDATETIME(), SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid, inserted.accounts_guid, inserted.element_prefix,
      inserted.element_account_number, inserted.element_last_number,
      inserted.element_max_number, inserted.element_allocation_size,
      inserted.element_reset_policy, inserted.element_sequence_status,
      inserted.element_pattern, inserted.element_display_format,
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
    args.get("pattern"),
    args.get("display_format"),
  )
  return await run_json_one(sql, params)


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
      element_reset_policy NVARCHAR(20),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE finance_numbers
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
