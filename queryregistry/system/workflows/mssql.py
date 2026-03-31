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
      element_is_active,
      element_max_concurrency,
      element_stall_threshold_seconds,
      element_created_on,
      element_modified_on
    FROM system_workflows
    WHERE element_name = ?
      AND element_status = 1
      AND element_is_active = 1
    ORDER BY element_version DESC, element_guid DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["name"],))


async def count_active_runs_by_workflow_name_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT COUNT(*) AS element_count
    FROM system_workflow_runs wr
    INNER JOIN system_workflows w
      ON w.element_guid = wr.workflows_guid
    WHERE wr.element_status IN (0, 1, 5, 6)
      AND w.element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["name"],))


async def list_workflows_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      w.element_guid,
      w.element_name,
      w.element_description,
      w.element_version,
      w.element_status,
      w.element_is_active,
      w.element_max_concurrency,
      w.element_stall_threshold_seconds,
      w.element_created_on,
      w.element_modified_on,
      (
        SELECT COUNT(*)
        FROM system_workflow_actions a
        WHERE a.workflows_guid = w.element_guid
      ) AS action_count
    FROM system_workflows w
    WHERE (? IS NULL OR w.element_status = ?)
    ORDER BY w.element_name, w.element_version DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args.get("status"), args.get("status")))


async def list_workflow_actions_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      a.element_guid,
      a.workflows_guid,
      a.element_name,
      a.element_description,
      a.functions_guid,
      a.dispositions_recid,
      a.element_rollback_functions_guid,
      a.element_sequence,
      a.element_is_optional,
      a.element_config,
      a.element_is_active,
      a.element_created_on,
      a.element_modified_on,
      f.element_module_attr,
      f.element_method_name,
      d.element_slug AS disposition_name
    FROM system_workflow_actions a
    INNER JOIN reflection_rpc_functions f
      ON f.element_guid = a.functions_guid
    INNER JOIN system_dispositions d
      ON d.recid = a.dispositions_recid
    WHERE a.workflows_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    ORDER BY a.element_sequence ASC, a.element_guid ASC
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
      element_current_action NVARCHAR(128),
      element_action_index INT,
      element_error NVARCHAR(MAX),
      element_trigger_type TINYINT,
      element_trigger_ref NVARCHAR(256),
      element_result NVARCHAR(MAX),
      element_created_by UNIQUEIDENTIFIER,
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    INSERT INTO system_workflow_runs (
      workflows_guid,
      element_status,
      element_payload,
      element_context,
      element_current_action,
      element_action_index,
      element_error,
      element_trigger_type,
      element_trigger_ref,
      element_result,
      element_created_by,
      element_started_on,
      element_ended_on
    )
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.workflows_guid,
      inserted.element_status,
      inserted.element_payload,
      inserted.element_context,
      inserted.element_current_action,
      inserted.element_action_index,
      inserted.element_error,
      inserted.element_trigger_type,
      inserted.element_trigger_ref,
      inserted.element_result,
      inserted.element_created_by,
      inserted.element_started_on,
      inserted.element_ended_on,
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
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
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
    args.get("current_action"),
    args.get("action_index", 0),
    args.get("error"),
    args.get("trigger_type"),
    args.get("trigger_ref"),
    args.get("result"),
    args.get("created_by"),
    args.get("started_on"),
    args.get("ended_on"),
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
      element_current_action,
      element_action_index,
      element_error,
      element_trigger_type,
      element_trigger_ref,
      element_result,
      element_created_by,
      element_started_on,
      element_ended_on,
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
      element_current_action,
      element_action_index,
      element_error,
      element_trigger_type,
      element_trigger_ref,
      element_result,
      element_created_by,
      element_started_on,
      element_ended_on,
      element_created_on,
      element_modified_on
    FROM system_workflow_runs
    WHERE (? IS NULL OR workflows_guid = TRY_CAST(? AS UNIQUEIDENTIFIER))
      AND (? IS NULL OR element_status = ?)
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(
    sql,
    (
      args.get("workflows_guid"),
      args.get("workflows_guid"),
      args.get("status"),
      args.get("status"),
    ),
  )


async def update_workflow_run_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args["recid"]
  setters: list[str] = []
  params: list[Any] = []

  for key, column in {
    "status": "element_status",
    "context": "element_context",
    "current_action": "element_current_action",
    "action_index": "element_action_index",
    "error": "element_error",
    "trigger_type": "element_trigger_type",
    "trigger_ref": "element_trigger_ref",
    "result": "element_result",
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
      element_current_action NVARCHAR(128),
      element_action_index INT,
      element_error NVARCHAR(MAX),
      element_trigger_type TINYINT,
      element_trigger_ref NVARCHAR(256),
      element_result NVARCHAR(MAX),
      element_created_by UNIQUEIDENTIFIER,
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
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
      inserted.element_current_action,
      inserted.element_action_index,
      inserted.element_error,
      inserted.element_trigger_type,
      inserted.element_trigger_ref,
      inserted.element_result,
      inserted.element_created_by,
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


async def create_workflow_run_action_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @inserted TABLE (
      recid BIGINT,
      element_guid UNIQUEIDENTIFIER,
      runs_recid BIGINT,
      actions_guid UNIQUEIDENTIFIER,
      element_status TINYINT,
      element_input NVARCHAR(MAX),
      element_output NVARCHAR(MAX),
      element_error NVARCHAR(MAX),
      element_sequence INT,
      element_retry_count INT,
      element_external_ref NVARCHAR(256),
      element_poll_interval_seconds INT,
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    INSERT INTO system_workflow_run_actions (
      runs_recid,
      actions_guid,
      element_status,
      element_input,
      element_output,
      element_error,
      element_sequence,
      element_retry_count,
      element_external_ref,
      element_poll_interval_seconds,
      element_started_on,
      element_ended_on
    )
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.runs_recid,
      inserted.actions_guid,
      inserted.element_status,
      inserted.element_input,
      inserted.element_output,
      inserted.element_error,
      inserted.element_sequence,
      inserted.element_retry_count,
      inserted.element_external_ref,
      inserted.element_poll_interval_seconds,
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
      ?,
      ?,
      ?,
      TRY_CAST(? AS DATETIMEOFFSET(7)),
      TRY_CAST(? AS DATETIMEOFFSET(7))
    );

    SELECT * FROM @inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(
    sql,
    (
      args["runs_recid"],
      args["actions_guid"],
      args.get("status", 0),
      args.get("input"),
      args.get("output"),
      args.get("error"),
      args.get("sequence", 0),
      args.get("retry_count", 0),
      args.get("external_ref"),
      args.get("poll_interval_seconds"),
      args.get("started_on"),
      args.get("ended_on"),
    ),
  )


async def update_workflow_run_action_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args["recid"]
  setters: list[str] = []
  params: list[Any] = []

  for key, column in {
    "status": "element_status",
    "output": "element_output",
    "error": "element_error",
    "retry_count": "element_retry_count",
    "external_ref": "element_external_ref",
    "poll_interval_seconds": "element_poll_interval_seconds",
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
      "SET NOCOUNT ON;\nSELECT * FROM system_workflow_run_actions WHERE recid = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;",
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
      actions_guid UNIQUEIDENTIFIER,
      element_status TINYINT,
      element_input NVARCHAR(MAX),
      element_output NVARCHAR(MAX),
      element_error NVARCHAR(MAX),
      element_sequence INT,
      element_retry_count INT,
      element_external_ref NVARCHAR(256),
      element_poll_interval_seconds INT,
      element_started_on DATETIMEOFFSET(7),
      element_ended_on DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE system_workflow_run_actions
    SET
      {set_sql}
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.runs_recid,
      inserted.actions_guid,
      inserted.element_status,
      inserted.element_input,
      inserted.element_output,
      inserted.element_error,
      inserted.element_sequence,
      inserted.element_retry_count,
      inserted.element_external_ref,
      inserted.element_poll_interval_seconds,
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


async def list_workflow_run_actions_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      runs_recid,
      actions_guid,
      element_status,
      element_input,
      element_output,
      element_error,
      element_sequence,
      element_retry_count,
      element_external_ref,
      element_poll_interval_seconds,
      element_started_on,
      element_ended_on,
      element_created_on,
      element_modified_on
    FROM system_workflow_run_actions
    WHERE runs_recid = ?
    ORDER BY element_sequence ASC, recid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["runs_recid"],))
