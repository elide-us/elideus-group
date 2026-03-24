"""MSSQL implementations for system batch jobs query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "create_history_v1",
  "delete_job_v1",
  "get_job_v1",
  "list_history_v1",
  "list_jobs_v1",
  "update_history_v1",
  "update_job_status_v1",
  "upsert_job_v1",
]


async def list_jobs_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
    SELECT
      recid,
      element_name,
      element_description,
      element_class,
      element_parameters,
      element_cron,
      element_recurrence_type,
      element_run_count_limit,
      element_run_until,
      element_total_runs,
      element_is_enabled,
      element_last_run,
      element_next_run,
      element_status,
      element_created_on,
      element_modified_on
    FROM system_batch_jobs
    ORDER BY element_name
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def get_job_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_description,
      element_class,
      element_parameters,
      element_cron,
      element_recurrence_type,
      element_run_count_limit,
      element_run_until,
      element_total_runs,
      element_is_enabled,
      element_last_run,
      element_next_run,
      element_status,
      element_created_on,
      element_modified_on
    FROM system_batch_jobs
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def upsert_job_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    DECLARE @inserted TABLE (
      recid BIGINT,
      element_name NVARCHAR(128),
      element_description NVARCHAR(512),
      element_class NVARCHAR(256),
      element_parameters NVARCHAR(MAX),
      element_cron NVARCHAR(64),
      element_recurrence_type TINYINT,
      element_run_count_limit INT,
      element_run_until DATETIMEOFFSET(7),
      element_total_runs INT,
      element_is_enabled BIT,
      element_last_run DATETIMEOFFSET(7),
      element_next_run DATETIMEOFFSET(7),
      element_status TINYINT,
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    IF ? IS NOT NULL AND EXISTS (SELECT 1 FROM system_batch_jobs WHERE recid = ?)
    BEGIN
      UPDATE system_batch_jobs
      SET
        element_name = ?,
        element_description = ?,
        element_class = ?,
        element_parameters = ?,
        element_cron = ?,
        element_recurrence_type = ?,
        element_run_count_limit = ?,
        element_run_until = TRY_CAST(? AS DATETIMEOFFSET(7)),
        element_is_enabled = ?,
        element_modified_on = SYSUTCDATETIME()
      WHERE recid = ?;

      SELECT
        recid,
        element_name,
        element_description,
        element_class,
        element_parameters,
        element_cron,
        element_recurrence_type,
        element_run_count_limit,
        element_run_until,
        element_total_runs,
        element_is_enabled,
        element_last_run,
        element_next_run,
        element_status,
        element_created_on,
        element_modified_on
      FROM system_batch_jobs
      WHERE recid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
    END
    ELSE
    BEGIN
      INSERT INTO system_batch_jobs (
        element_name,
        element_description,
        element_class,
        element_parameters,
        element_cron,
        element_recurrence_type,
        element_run_count_limit,
        element_run_until,
        element_is_enabled,
        element_created_on,
        element_modified_on
      )
      OUTPUT
        inserted.recid,
        inserted.element_name,
        inserted.element_description,
        inserted.element_class,
        inserted.element_parameters,
        inserted.element_cron,
        inserted.element_recurrence_type,
        inserted.element_run_count_limit,
        inserted.element_run_until,
        inserted.element_total_runs,
        inserted.element_is_enabled,
        inserted.element_last_run,
        inserted.element_next_run,
        inserted.element_status,
        inserted.element_created_on,
        inserted.element_modified_on
      INTO @inserted
      VALUES (
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        TRY_CAST(? AS DATETIMEOFFSET(7)),
        ?,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      );

      SELECT
        recid,
        element_name,
        element_description,
        element_class,
        element_parameters,
        element_cron,
        element_recurrence_type,
        element_run_count_limit,
        element_run_until,
        element_total_runs,
        element_is_enabled,
        element_last_run,
        element_next_run,
        element_status,
        element_created_on,
        element_modified_on
      FROM @inserted
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
    END
  """
  params = (
    args.get("recid"),
    args.get("recid"),
    args["name"],
    args.get("description"),
    args["class_path"],
    args.get("parameters"),
    args["cron"],
    args["recurrence_type"],
    args.get("run_count_limit"),
    args.get("run_until"),
    args["is_enabled"],
    args.get("recid"),
    args.get("recid"),
    args["name"],
    args.get("description"),
    args["class_path"],
    args.get("parameters"),
    args["cron"],
    args["recurrence_type"],
    args.get("run_count_limit"),
    args.get("run_until"),
    args["is_enabled"],
  )
  return await run_json_one(sql, params)


async def delete_job_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM system_batch_jobs
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))


async def list_history_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT TOP (50)
      recid,
      jobs_recid,
      element_started_on,
      element_ended_on,
      element_status,
      element_error,
      element_result,
      element_created_on
    FROM system_batch_job_history
    WHERE jobs_recid = ?
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["jobs_recid"],))


async def create_history_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    DECLARE @inserted TABLE (
      recid BIGINT,
      jobs_recid BIGINT,
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_status TINYINT,
      element_error NVARCHAR(MAX),
      element_result NVARCHAR(MAX),
      element_created_on DATETIMEOFFSET(7)
    );

    INSERT INTO system_batch_job_history (jobs_recid)
    OUTPUT
      inserted.recid,
      inserted.jobs_recid,
      inserted.element_started_on,
      inserted.element_ended_on,
      inserted.element_status,
      inserted.element_error,
      inserted.element_result,
      inserted.element_created_on
    INTO @inserted
    VALUES (?);

    SELECT
      recid,
      jobs_recid,
      element_started_on,
      element_ended_on,
      element_status,
      element_error,
      element_result,
      element_created_on
    FROM @inserted
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["jobs_recid"],))


async def update_history_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    UPDATE system_batch_job_history
    SET
      element_ended_on = SYSUTCDATETIME(),
      element_status = ?,
      element_error = ?,
      element_result = ?
    WHERE recid = ?;
  """
  params = (args["status"], args.get("error"), args.get("result"), args["recid"])
  return await run_exec(sql, params)


async def update_job_status_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    UPDATE system_batch_jobs
    SET
      element_status = ?,
      element_total_runs = COALESCE(?, element_total_runs),
      element_last_run = TRY_CAST(? AS DATETIMEOFFSET(7)),
      element_next_run = TRY_CAST(? AS DATETIMEOFFSET(7)),
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?;
  """
  params = (
    args["status"],
    args.get("total_runs"),
    args.get("last_run"),
    args.get("next_run"),
    args["recid"],
  )
  return await run_exec(sql, params)
