"""MSSQL implementations for finance accounts query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = ["delete_v1", "get_v1", "list_children_v1", "list_v1", "upsert_v1"]


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
    SELECT
      account.element_guid,
      account.element_number,
      account.element_name,
      account.element_type,
      account.element_parent,
      parent.element_number AS element_parent_number,
      parent.element_name AS element_parent_name,
      account.is_posting,
      account.element_status,
      account.element_created_on,
      account.element_modified_on
    FROM finance_accounts AS account
    LEFT JOIN finance_accounts AS parent
      ON parent.element_guid = account.element_parent
    ORDER BY account.element_number
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      account.element_guid,
      account.element_number,
      account.element_name,
      account.element_type,
      account.element_parent,
      parent.element_number AS element_parent_number,
      parent.element_name AS element_parent_name,
      account.is_posting,
      account.element_status,
      account.element_created_on,
      account.element_modified_on
    FROM finance_accounts AS account
    LEFT JOIN finance_accounts AS parent
      ON parent.element_guid = account.element_parent
    WHERE account.element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"],))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    MERGE finance_accounts AS target
    USING (
      SELECT
        COALESCE(TRY_CAST(? AS UNIQUEIDENTIFIER), NEWID()) AS element_guid,
        ? AS element_number,
        ? AS element_name,
        ? AS element_type,
        TRY_CAST(? AS UNIQUEIDENTIFIER) AS element_parent,
        ? AS is_posting,
        ? AS element_status
    ) AS source
    ON target.element_guid = source.element_guid
    WHEN MATCHED THEN
      UPDATE SET
        target.element_number = source.element_number,
        target.element_name = source.element_name,
        target.element_type = source.element_type,
        target.element_parent = source.element_parent,
        target.is_posting = source.is_posting,
        target.element_status = source.element_status,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_guid,
        element_number,
        element_name,
        element_type,
        element_parent,
        is_posting,
        element_status,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_guid,
        source.element_number,
        source.element_name,
        source.element_type,
        source.element_parent,
        source.is_posting,
        source.element_status,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.element_guid,
      inserted.element_number,
      inserted.element_name,
      inserted.element_type,
      inserted.element_parent,
      inserted.is_posting,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("guid"),
    args["number"],
    args["name"],
    args["account_type"],
    args.get("parent"),
    args["is_posting"],
    args["status"],
  )
  return await run_json_one(sql, params)


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_accounts
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (args["guid"],))


async def list_children_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      element_guid,
      element_number,
      element_name,
      element_type,
      element_parent,
      is_posting,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_accounts
    WHERE element_parent = ?
    ORDER BY element_number
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["parent_guid"],))
