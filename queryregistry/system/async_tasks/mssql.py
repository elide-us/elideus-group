from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one


async def create_task_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @inserted TABLE (
      recid BIGINT,
      element_guid UNIQUEIDENTIFIER,
      element_handler_type NVARCHAR(20),
      element_handler_name NVARCHAR(256),
      element_payload NVARCHAR(MAX),
      element_status TINYINT,
      element_result NVARCHAR(MAX),
      element_error NVARCHAR(MAX),
      element_current_step NVARCHAR(128),
      element_step_index INT,
      element_max_retries INT,
      element_retry_count INT,
      element_poll_interval_seconds INT,
      element_timeout_seconds INT,
      element_timeout_at DATETIMEOFFSET(7),
      element_external_id NVARCHAR(512),
      element_source_type NVARCHAR(64),
      element_source_id NVARCHAR(256),
      element_created_by UNIQUEIDENTIFIER,
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    INSERT INTO system_async_tasks (
      element_handler_type,
      element_handler_name,
      element_payload,
      element_status,
      element_max_retries,
      element_retry_count,
      element_poll_interval_seconds,
      element_timeout_seconds,
      element_timeout_at,
      element_external_id,
      element_source_type,
      element_source_id,
      element_created_by
    )
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.element_handler_type,
      inserted.element_handler_name,
      inserted.element_payload,
      inserted.element_status,
      inserted.element_result,
      inserted.element_error,
      inserted.element_current_step,
      inserted.element_step_index,
      inserted.element_max_retries,
      inserted.element_retry_count,
      inserted.element_poll_interval_seconds,
      inserted.element_timeout_seconds,
      inserted.element_timeout_at,
      inserted.element_external_id,
      inserted.element_source_type,
      inserted.element_source_id,
      inserted.element_created_by,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @inserted
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRY_CAST(? AS DATETIMEOFFSET(7)), ?, ?, ?, TRY_CAST(? AS UNIQUEIDENTIFIER));

    SELECT * FROM @inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["handler_type"],
    args["handler_name"],
    args.get("payload"),
    args.get("status", 0),
    args.get("max_retries", 0),
    args.get("retry_count", 0),
    args.get("poll_interval_seconds"),
    args.get("timeout_seconds"),
    args.get("timeout_at"),
    args.get("external_id"),
    args.get("source_type"),
    args.get("source_id"),
    args.get("created_by"),
  )
  return await run_json_one(sql, params)


async def get_task_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      element_handler_type,
      element_handler_name,
      element_payload,
      element_status,
      element_result,
      element_error,
      element_current_step,
      element_step_index,
      element_max_retries,
      element_retry_count,
      element_poll_interval_seconds,
      element_timeout_seconds,
      element_timeout_at,
      element_external_id,
      element_source_type,
      element_source_id,
      element_created_by,
      element_created_on,
      element_modified_on
    FROM system_async_tasks
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"],))


async def list_tasks_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      element_handler_type,
      element_handler_name,
      element_payload,
      element_status,
      element_result,
      element_error,
      element_current_step,
      element_step_index,
      element_max_retries,
      element_retry_count,
      element_poll_interval_seconds,
      element_timeout_seconds,
      element_timeout_at,
      element_external_id,
      element_source_type,
      element_source_id,
      element_created_by,
      element_created_on,
      element_modified_on
    FROM system_async_tasks
    WHERE (? IS NULL OR element_status = ?)
      AND (? IS NULL OR element_handler_type = ?)
      AND (? IS NULL OR element_handler_name = ?)
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("status"),
    args.get("status"),
    args.get("handler_type"),
    args.get("handler_type"),
    args.get("handler_name"),
    args.get("handler_name"),
  )
  return await run_json_many(sql, params)


async def update_task_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args["recid"]
  setters: list[str] = []
  params: list[Any] = []

  column_map = {
    "status": "element_status",
    "error": "element_error",
    "current_step": "element_current_step",
    "step_index": "element_step_index",
    "retry_count": "element_retry_count",
    "poll_interval_seconds": "element_poll_interval_seconds",
    "timeout_seconds": "element_timeout_seconds",
    "timeout_at": "element_timeout_at",
    "external_id": "element_external_id",
  }

  for key, column in column_map.items():
    if key in args:
      if key == "timeout_at":
        setters.append(f"{column} = TRY_CAST(? AS DATETIMEOFFSET(7))")
      else:
        setters.append(f"{column} = ?")
      params.append(args.get(key))

  if "result" in args:
    setters.append("element_result = ?")
    value = args.get("result")
    if isinstance(value, (dict, list)):
      value = json.dumps(value)
    params.append(value)

  if not setters:
    return await run_json_one(
      "SET NOCOUNT ON;\nSELECT * FROM system_async_tasks WHERE recid = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;",
      (recid,),
    )

  setters.append("element_modified_on = SYSUTCDATETIME()")
  set_sql = ",\n      ".join(setters)
  sql = f"""
    SET NOCOUNT ON;

    DECLARE @updated TABLE (
      recid BIGINT,
      element_guid UNIQUEIDENTIFIER,
      element_handler_type NVARCHAR(20),
      element_handler_name NVARCHAR(256),
      element_payload NVARCHAR(MAX),
      element_status TINYINT,
      element_result NVARCHAR(MAX),
      element_error NVARCHAR(MAX),
      element_current_step NVARCHAR(128),
      element_step_index INT,
      element_max_retries INT,
      element_retry_count INT,
      element_poll_interval_seconds INT,
      element_timeout_seconds INT,
      element_timeout_at DATETIMEOFFSET(7),
      element_external_id NVARCHAR(512),
      element_source_type NVARCHAR(64),
      element_source_id NVARCHAR(256),
      element_created_by UNIQUEIDENTIFIER,
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE system_async_tasks
    SET
      {set_sql}
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.element_handler_type,
      inserted.element_handler_name,
      inserted.element_payload,
      inserted.element_status,
      inserted.element_result,
      inserted.element_error,
      inserted.element_current_step,
      inserted.element_step_index,
      inserted.element_max_retries,
      inserted.element_retry_count,
      inserted.element_poll_interval_seconds,
      inserted.element_timeout_seconds,
      inserted.element_timeout_at,
      inserted.element_external_id,
      inserted.element_source_type,
      inserted.element_source_id,
      inserted.element_created_by,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @updated
    WHERE recid = ?;

    SELECT * FROM @updated FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params.append(recid)
  return await run_json_one(sql, tuple(params))


async def create_task_event_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    INSERT INTO system_async_task_events (
      tasks_recid,
      element_event_type,
      element_step_name,
      element_detail
    )
    VALUES (?, ?, ?, ?);
  """
  return await run_exec(
    sql,
    (args["tasks_recid"], args["event_type"], args.get("step_name"), args.get("detail")),
  )


async def list_task_events_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      tasks_recid,
      element_event_type,
      element_step_name,
      element_detail,
      element_created_on
    FROM system_async_task_events
    WHERE tasks_recid = ?
    ORDER BY element_created_on ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["tasks_recid"],))
