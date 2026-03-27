from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one


async def get_active_workflow_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT TOP 1
      element_guid,
      element_name,
      element_description,
      element_version,
      element_status,
      element_created_on,
      element_modified_on
    FROM system_workflows
    WHERE element_name = ?
      AND element_status = 1
    ORDER BY element_version DESC, element_guid DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["name"],))


async def list_workflow_steps_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      element_guid,
      workflows_guid,
      element_name,
      element_description,
      element_step_type,
      element_disposition,
      element_class_path,
      element_sequence,
      element_is_optional,
      element_timeout_seconds,
      element_config,
      element_created_on,
      element_modified_on
    FROM system_workflow_steps
    WHERE workflows_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    ORDER BY element_sequence ASC, element_guid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["workflows_guid"],))


async def create_workflow_run_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @inserted TABLE (
      recid BIGINT,
      element_guid UNIQUEIDENTIFIER,
      workflows_guid UNIQUEIDENTIFIER,
      element_status TINYINT,
      element_payload NVARCHAR(MAX),
      element_context NVARCHAR(MAX),
      element_current_step NVARCHAR(128),
      element_step_index INT,
      element_error NVARCHAR(MAX),
      element_source_type NVARCHAR(64),
      element_source_id NVARCHAR(256),
      element_created_by UNIQUEIDENTIFIER,
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_timeout_at DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    INSERT INTO system_workflow_runs (
      workflows_guid,
      element_status,
      element_payload,
      element_context,
      element_current_step,
      element_step_index,
      element_error,
      element_source_type,
      element_source_id,
      element_created_by,
      element_started_on,
      element_ended_on,
      element_timeout_at
    )
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.workflows_guid,
      inserted.element_status,
      inserted.element_payload,
      inserted.element_context,
      inserted.element_current_step,
      inserted.element_step_index,
      inserted.element_error,
      inserted.element_source_type,
      inserted.element_source_id,
      inserted.element_created_by,
      inserted.element_started_on,
      inserted.element_ended_on,
      inserted.element_timeout_at,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @inserted
    VALUES (
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      TRY_CAST(? AS DATETIMEOFFSET(7)),
      TRY_CAST(? AS DATETIMEOFFSET(7)),
      TRY_CAST(? AS DATETIMEOFFSET(7))
    );

    SELECT * FROM @inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["workflows_guid"],
    args.get("status", 0),
    args.get("payload"),
    args.get("context"),
    args.get("current_step"),
    args.get("step_index", 0),
    args.get("error"),
    args.get("source_type"),
    args.get("source_id"),
    args.get("created_by"),
    args.get("started_on"),
    args.get("ended_on"),
    args.get("timeout_at"),
  )
  return await run_json_one(sql, params)


async def get_workflow_run_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      workflows_guid,
      element_status,
      element_payload,
      element_context,
      element_current_step,
      element_step_index,
      element_error,
      element_source_type,
      element_source_id,
      element_created_by,
      element_started_on,
      element_ended_on,
      element_timeout_at,
      element_created_on,
      element_modified_on
    FROM system_workflow_runs
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"],))


async def list_workflow_runs_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      workflows_guid,
      element_status,
      element_payload,
      element_context,
      element_current_step,
      element_step_index,
      element_error,
      element_source_type,
      element_source_id,
      element_created_by,
      element_started_on,
      element_ended_on,
      element_timeout_at,
      element_created_on,
      element_modified_on
    FROM system_workflow_runs
    WHERE (? IS NULL OR workflows_guid = TRY_CAST(? AS UNIQUEIDENTIFIER))
      AND (? IS NULL OR element_status = ?)
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("workflows_guid"),
    args.get("workflows_guid"),
    args.get("status"),
    args.get("status"),
  )
  return await run_json_many(sql, params)


async def update_workflow_run_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args["recid"]
  setters: list[str] = []
  params: list[Any] = []

  simple_columns = {
    "status": "element_status",
    "context": "element_context",
    "current_step": "element_current_step",
    "step_index": "element_step_index",
    "error": "element_error",
  }
  for key, column in simple_columns.items():
    if key in args:
      setters.append(f"{column} = ?")
      params.append(args.get(key))

  for key, column in {
    "started_on": "element_started_on",
    "ended_on": "element_ended_on",
  }.items():
    if key in args:
      setters.append(f"{column} = TRY_CAST(? AS DATETIMEOFFSET(7))")
      params.append(args.get(key))

  if not setters:
    return await run_json_one(
      "SET NOCOUNT ON;\nSELECT * FROM system_workflow_runs WHERE recid = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;",
      (recid,),
    )

  setters.append("element_modified_on = SYSUTCDATETIME()")
  set_sql = ",\n      ".join(setters)

  sql = f"""
    SET NOCOUNT ON;

    DECLARE @updated TABLE (
      recid BIGINT,
      element_guid UNIQUEIDENTIFIER,
      workflows_guid UNIQUEIDENTIFIER,
      element_status TINYINT,
      element_payload NVARCHAR(MAX),
      element_context NVARCHAR(MAX),
      element_current_step NVARCHAR(128),
      element_step_index INT,
      element_error NVARCHAR(MAX),
      element_source_type NVARCHAR(64),
      element_source_id NVARCHAR(256),
      element_created_by UNIQUEIDENTIFIER,
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_timeout_at DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE system_workflow_runs
    SET
      {set_sql}
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.workflows_guid,
      inserted.element_status,
      inserted.element_payload,
      inserted.element_context,
      inserted.element_current_step,
      inserted.element_step_index,
      inserted.element_error,
      inserted.element_source_type,
      inserted.element_source_id,
      inserted.element_created_by,
      inserted.element_started_on,
      inserted.element_ended_on,
      inserted.element_timeout_at,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @updated
    WHERE recid = ?;

    SELECT * FROM @updated FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params.append(recid)
  return await run_json_one(sql, tuple(params))


async def create_workflow_run_step_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @inserted TABLE (
      recid BIGINT,
      element_guid UNIQUEIDENTIFIER,
      runs_recid BIGINT,
      steps_guid UNIQUEIDENTIFIER,
      element_status TINYINT,
      element_disposition NVARCHAR(16),
      element_input NVARCHAR(MAX),
      element_output NVARCHAR(MAX),
      element_error NVARCHAR(MAX),
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    INSERT INTO system_workflow_run_steps (
      runs_recid,
      steps_guid,
      element_status,
      element_disposition,
      element_input,
      element_output,
      element_error,
      element_started_on,
      element_ended_on
    )
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.runs_recid,
      inserted.steps_guid,
      inserted.element_status,
      inserted.element_disposition,
      inserted.element_input,
      inserted.element_output,
      inserted.element_error,
      inserted.element_started_on,
      inserted.element_ended_on,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @inserted
    VALUES (
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      ?,
      ?,
      ?,
      ?,
      ?,
      TRY_CAST(? AS DATETIMEOFFSET(7)),
      TRY_CAST(? AS DATETIMEOFFSET(7))
    );

    SELECT * FROM @inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["runs_recid"],
    args["steps_guid"],
    args.get("status", 0),
    args["disposition"],
    args.get("input"),
    args.get("output"),
    args.get("error"),
    args.get("started_on"),
    args.get("ended_on"),
  )
  return await run_json_one(sql, params)


async def update_workflow_run_step_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args["recid"]
  setters: list[str] = []
  params: list[Any] = []

  for key, column in {
    "status": "element_status",
    "output": "element_output",
    "error": "element_error",
  }.items():
    if key in args:
      setters.append(f"{column} = ?")
      params.append(args.get(key))

  for key, column in {
    "started_on": "element_started_on",
    "ended_on": "element_ended_on",
  }.items():
    if key in args:
      setters.append(f"{column} = TRY_CAST(? AS DATETIMEOFFSET(7))")
      params.append(args.get(key))

  if not setters:
    return await run_json_one(
      "SET NOCOUNT ON;\nSELECT * FROM system_workflow_run_steps WHERE recid = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;",
      (recid,),
    )

  setters.append("element_modified_on = SYSUTCDATETIME()")
  set_sql = ",\n      ".join(setters)

  sql = f"""
    SET NOCOUNT ON;

    DECLARE @updated TABLE (
      recid BIGINT,
      element_guid UNIQUEIDENTIFIER,
      runs_recid BIGINT,
      steps_guid UNIQUEIDENTIFIER,
      element_status TINYINT,
      element_disposition NVARCHAR(16),
      element_input NVARCHAR(MAX),
      element_output NVARCHAR(MAX),
      element_error NVARCHAR(MAX),
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE system_workflow_run_steps
    SET
      {set_sql}
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.runs_recid,
      inserted.steps_guid,
      inserted.element_status,
      inserted.element_disposition,
      inserted.element_input,
      inserted.element_output,
      inserted.element_error,
      inserted.element_started_on,
      inserted.element_ended_on,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @updated
    WHERE recid = ?;

    SELECT * FROM @updated FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params.append(recid)
  return await run_json_one(sql, tuple(params))


async def list_workflow_run_steps_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      runs_recid,
      steps_guid,
      element_status,
      element_disposition,
      element_input,
      element_output,
      element_error,
      element_started_on,
      element_ended_on,
      element_created_on,
      element_modified_on
    FROM system_workflow_run_steps
    WHERE runs_recid = ?
    ORDER BY element_created_on ASC, recid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["runs_recid"],))
