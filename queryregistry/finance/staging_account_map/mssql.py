"""MSSQL implementations for finance staging account map query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "delete_account_map_v1",
  "get_account_map_v1",
  "list_account_map_v1",
  "resolve_account_v1",
  "upsert_account_map_v1",
]


async def list_account_map_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
    SELECT
      map.recid,
      map.element_service_pattern,
      map.element_meter_pattern,
      map.accounts_guid,
      account.element_number AS account_number,
      account.element_name AS account_name,
      map.element_priority,
      map.element_description,
      map.element_status,
      map.element_created_on,
      map.element_modified_on
    FROM finance_staging_account_map AS map
    INNER JOIN finance_accounts AS account
      ON account.element_guid = map.accounts_guid
    ORDER BY map.element_priority DESC, map.recid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def get_account_map_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      map.recid,
      map.element_service_pattern,
      map.element_meter_pattern,
      map.accounts_guid,
      account.element_number AS account_number,
      account.element_name AS account_name,
      map.element_priority,
      map.element_description,
      map.element_status,
      map.element_created_on,
      map.element_modified_on
    FROM finance_staging_account_map AS map
    INNER JOIN finance_accounts AS account
      ON account.element_guid = map.accounts_guid
    WHERE map.recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def upsert_account_map_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    MERGE finance_staging_account_map AS target
    USING (
      SELECT
        TRY_CAST(? AS BIGINT) AS recid,
        ? AS element_service_pattern,
        ? AS element_meter_pattern,
        TRY_CAST(? AS UNIQUEIDENTIFIER) AS accounts_guid,
        ? AS element_priority,
        ? AS element_description,
        ? AS element_status
    ) AS source
    ON target.recid = source.recid
    WHEN MATCHED THEN
      UPDATE SET
        target.element_service_pattern = source.element_service_pattern,
        target.element_meter_pattern = source.element_meter_pattern,
        target.accounts_guid = source.accounts_guid,
        target.element_priority = source.element_priority,
        target.element_description = source.element_description,
        target.element_status = source.element_status,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_service_pattern,
        element_meter_pattern,
        accounts_guid,
        element_priority,
        element_description,
        element_status,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_service_pattern,
        source.element_meter_pattern,
        source.accounts_guid,
        source.element_priority,
        source.element_description,
        source.element_status,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid,
      inserted.element_service_pattern,
      inserted.element_meter_pattern,
      inserted.accounts_guid,
      inserted.element_priority,
      inserted.element_description,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("recid"),
    args["element_service_pattern"],
    args.get("element_meter_pattern"),
    args["accounts_guid"],
    args["element_priority"],
    args.get("element_description"),
    args["element_status"],
  )
  return await run_json_one(sql, params)


async def delete_account_map_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_staging_account_map
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))


async def resolve_account_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT TOP (1)
      map.accounts_guid
    FROM finance_staging_account_map AS map
    WHERE map.element_status = 1
      AND (map.element_service_pattern = ? OR map.element_service_pattern = '*')
      AND (
        map.element_meter_pattern IS NULL
        OR ? LIKE REPLACE(map.element_meter_pattern, '*', '%')
      )
    ORDER BY
      CASE
        WHEN map.element_service_pattern = ? THEN 0
        WHEN map.element_service_pattern = '*' THEN 1
        ELSE 2
      END,
      map.element_priority DESC,
      map.recid ASC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  meter_category = args.get("meter_category") or ""
  params = (
    args["service_name"],
    meter_category,
    args["service_name"],
  )
  return await run_json_one(sql, params)
