from fastapi import HTTPException, Request

from queryregistry.system.scheduled_tasks import (
  get_task_request,
  get_workflow_name_by_guid_request,
  list_all_tasks_request,
  list_task_history_request,
)
from queryregistry.system.scheduled_tasks.models import (
  GetTaskParams,
  GetWorkflowNameByGuidParams,
  ListAllTasksParams,
  ListTaskHistoryParams,
)
from rpc.helpers import unbox_request
from rpc.system.workflows.models import SystemWorkflowRunItem1
from server.models import RPCResponse
from server.modules.workflow_module import WorkflowModule

from .models import (
  ScheduledTaskGetRequest1,
  ScheduledTaskHistoryItem1,
  ScheduledTaskHistoryList1,
  ScheduledTaskItem1,
  ScheduledTaskList1,
  ScheduledTaskListHistoryRequest1,
  ScheduledTaskRunNowRequest1,
)


async def system_scheduled_tasks_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.scheduler
  await module.on_ready()
  db = request.app.state.db
  await db.on_ready()
  res = await db.run(list_all_tasks_request(ListAllTasksParams()))
  rows = [_map_task(dict(row)) for row in res.rows]
  payload = ScheduledTaskList1(tasks=[ScheduledTaskItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_scheduled_tasks_get_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = ScheduledTaskGetRequest1(**(rpc_request.payload or {}))
  db = request.app.state.db
  await db.on_ready()
  res = await db.run(get_task_request(GetTaskParams(recid=params.recid)))
  if not res.rows:
    raise HTTPException(status_code=404, detail="Scheduled task not found")
  row = _map_task(dict(res.rows[0]))
  payload = ScheduledTaskItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_scheduled_tasks_list_history_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = ScheduledTaskListHistoryRequest1(**(rpc_request.payload or {}))
  db = request.app.state.db
  await db.on_ready()
  res = await db.run(list_task_history_request(ListTaskHistoryParams(tasks_recid=params.tasks_recid)))
  rows = [_map_history(dict(row)) for row in res.rows]
  payload = ScheduledTaskHistoryList1(history=[ScheduledTaskHistoryItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_scheduled_tasks_run_now_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ScheduledTaskRunNowRequest1(**(rpc_request.payload or {}))
  db = request.app.state.db
  await db.on_ready()
  res = await db.run(get_task_request(GetTaskParams(recid=params.recid)))
  if not res.rows:
    raise HTTPException(status_code=404, detail="Scheduled task not found")
  task = dict(res.rows[0])

  name_res = await db.run(
    get_workflow_name_by_guid_request(
      GetWorkflowNameByGuidParams(guid=str(task.get("workflows_guid") or ""))
    )
  )
  workflow_name = str((dict(name_res.rows[0]) if name_res.rows else {}).get("element_name") or "")

  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  run = await module.submit(
    workflow_name=workflow_name,
    payload={},
    trigger_type_code=0,
    trigger_ref=str(params.recid),
    created_by=auth_ctx.user_guid,
  )
  payload = SystemWorkflowRunItem1(**run)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


def _map_task(row: dict) -> dict:
  return {
    "recid": row.get("recid"),
    "name": row.get("element_name"),
    "description": row.get("element_description"),
    "workflows_guid": row.get("workflows_guid"),
    "payload_template": row.get("element_payload_template"),
    "cron": row.get("element_cron"),
    "recurrence_type": row.get("element_recurrence_type"),
    "run_count_limit": row.get("element_run_count_limit"),
    "run_until": row.get("element_run_until"),
    "total_runs": row.get("element_total_runs"),
    "status": row.get("element_status"),
    "last_run": row.get("element_last_run"),
    "next_run": row.get("element_next_run"),
    "created_on": row.get("element_created_on"),
    "modified_on": row.get("element_modified_on"),
  }


def _map_history(row: dict) -> dict:
  return {
    "recid": row.get("recid"),
    "tasks_recid": row.get("tasks_recid"),
    "runs_recid": row.get("runs_recid"),
    "fired_on": row.get("element_fired_on"),
    "error": row.get("element_error"),
    "created_on": row.get("element_created_on"),
  }
