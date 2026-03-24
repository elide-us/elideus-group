from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one


async def list_purge_logs_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      vendors_recid,
      element_period_key,
      element_purged_keys,
      element_purged_count,
      element_purged_on,
      element_created_on,
      element_modified_on
    FROM finance_staging_purge_log
    WHERE (? IS NULL OR vendors_recid = ?)
    ORDER BY element_period_key DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  vendors_recid = args.get("vendors_recid")
  return await run_json_many(sql, (vendors_recid, vendors_recid))


async def get_purge_log_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      vendors_recid,
      element_period_key,
      element_purged_keys,
      element_purged_count,
      element_purged_on,
      element_created_on,
      element_modified_on
    FROM finance_staging_purge_log
    WHERE vendors_recid = ?
      AND element_period_key = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["vendors_recid"], args["period_key"]))


async def check_purged_key_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT TOP (1) 1 AS found
    FROM finance_staging_purge_log log
    CROSS APPLY OPENJSON(log.element_purged_keys, '$.batch_purged') AS j
    WHERE log.vendors_recid = ?
      AND j.value = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["vendors_recid"], args["key"]))


async def upsert_purge_log_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    MERGE finance_staging_purge_log AS target
    USING (
      SELECT ? AS vendors_recid, ? AS period_key
    ) AS source
    ON target.vendors_recid = source.vendors_recid
      AND target.element_period_key = source.period_key
    WHEN MATCHED THEN
      UPDATE SET
        element_purged_keys = ?,
        element_purged_count = ?,
        element_purged_on = SYSUTCDATETIME(),
        element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (vendors_recid, element_period_key, element_purged_keys, element_purged_count)
      VALUES (?, ?, ?, ?);
  """
  return await run_exec(
    sql,
    (
      args["vendors_recid"],
      args["period_key"],
      args["purged_keys_json"],
      args["purged_count"],
      args["vendors_recid"],
      args["period_key"],
      args["purged_keys_json"],
      args["purged_count"],
    ),
  )
