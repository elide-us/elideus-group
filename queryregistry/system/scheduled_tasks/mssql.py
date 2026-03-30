from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one


async def list_enabled_due_tasks_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM system_scheduled_tasks
    WHERE element_status = 1
      AND element_next_run <= TRY_CAST(? AS DATETIMEOFFSET(7))
    ORDER BY element_next_run ASC, recid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["now"],))


async def update_scheduled_task_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args["recid"]
  setters: list[str] = []
  params: list[Any] = []

  if "total_runs" in args:
    setters.append("element_total_runs = ?")
    params.append(args.get("total_runs"))

  if "status" in args:
    setters.append("element_status = ?")
    params.append(args.get("status"))

  if "last_run" in args:
    setters.append("element_last_run = TRY_CAST(? AS DATETIMEOFFSET(7))")
    params.append(args.get("last_run"))

  if "next_run" in args:
    setters.append("element_next_run = TRY_CAST(? AS DATETIMEOFFSET(7))")
    params.append(args.get("next_run"))

  if not setters:
    return await run_json_one(
      "SET NOCOUNT ON;\nSELECT * FROM system_scheduled_tasks WHERE recid = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;",
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
      element_name NVARCHAR(128),
      element_description NVARCHAR(MAX),
      element_cron NVARCHAR(128),
      element_payload_template NVARCHAR(MAX),
      element_status TINYINT,
      element_run_count_limit INT,
      element_run_until DATETIMEOFFSET(7),
      element_total_runs INT,
      element_last_run DATETIMEOFFSET(7),
      element_next_run DATETIMEOFFSET(7),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    UPDATE system_scheduled_tasks
    SET
      {set_sql}
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.workflows_guid,
      inserted.element_name,
      inserted.element_description,
      inserted.element_cron,
      inserted.element_payload_template,
      inserted.element_status,
      inserted.element_run_count_limit,
      inserted.element_run_until,
      inserted.element_total_runs,
      inserted.element_last_run,
      inserted.element_next_run,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @updated
    WHERE recid = ?;

    SELECT * FROM @updated FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params.append(recid)
  return await run_json_one(sql, tuple(params))


async def create_scheduled_task_history_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @inserted TABLE (
      recid BIGINT,
      tasks_recid BIGINT,
      runs_recid BIGINT,
      element_fired_on DATETIMEOFFSET(7),
      element_error NVARCHAR(MAX),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    INSERT INTO system_scheduled_task_history (
      tasks_recid,
      runs_recid,
      element_fired_on,
      element_error
    )
    OUTPUT
      inserted.recid,
      inserted.tasks_recid,
      inserted.runs_recid,
      inserted.element_fired_on,
      inserted.element_error,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @inserted
    VALUES (
      ?,
      ?,
      SYSUTCDATETIME(),
      ?
    );

    SELECT * FROM @inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(
    sql,
    (args["tasks_recid"], args.get("runs_recid"), args.get("error")),
  )


async def get_workflow_name_by_guid_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT TOP 1 element_name
    FROM system_workflows
    WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    ORDER BY element_version DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guid"],))
