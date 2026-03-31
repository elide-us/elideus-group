from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.workflow_module import WorkflowModule

from .models import (
  SystemWorkflowActionItem1,
  SystemWorkflowDetail1,
  SystemWorkflowGetRequest1,
  SystemWorkflowItem1,
  SystemWorkflowList1,
  SystemWorkflowListRequest1,
  SystemWorkflowRunActionItem1,
  SystemWorkflowRunActionList1,
  SystemWorkflowRunActionListRequest1,
  SystemWorkflowRunCancelRequest1,
  SystemWorkflowRunGetRequest1,
  SystemWorkflowRunItem1,
  SystemWorkflowRunList1,
  SystemWorkflowRunListRequest1,
  SystemWorkflowRunResumeRequest1,
  SystemWorkflowRunRetryActionRequest1,
  SystemWorkflowRunRollbackRequest1,
  SystemWorkflowRunSubmitRequest1,
  SystemWorkflowScanStallsRequest1,
  SystemWorkflowScanStallsResponse1,
)


async def system_workflows_list_workflows_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowListRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  rows = await module.list_workflows(status=params.status)
  payload = SystemWorkflowList1(workflows=[SystemWorkflowItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_get_workflow_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowGetRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  workflow = await module.get_workflow(params.name)
  if not workflow:
    raise HTTPException(status_code=404, detail=f"Workflow '{params.name}' not found")
  actions = await module.list_actions(workflow["guid"])
  payload = SystemWorkflowDetail1(
    guid=workflow["guid"],
    name=workflow["name"],
    description=workflow.get("description"),
    version=workflow["version"],
    status=workflow["status"],
    actions=[SystemWorkflowActionItem1(**a) for a in actions],
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_list_runs_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunListRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  rows = await module.list(status=params.status)
  payload = SystemWorkflowRunList1(runs=[SystemWorkflowRunItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_get_run_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunGetRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  row = await module.get(params.guid)
  if not row:
    raise HTTPException(status_code=404, detail="Workflow run not found")
  payload = SystemWorkflowRunItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_submit_run_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = SystemWorkflowRunSubmitRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  row = await module.submit(
    workflow_name=params.workflow_name,
    payload=params.payload,
    trigger_type_code=params.trigger_type,
    trigger_ref=params.trigger_ref,
    created_by=auth_ctx.user_guid,
  )
  payload = SystemWorkflowRunItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_cancel_run_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunCancelRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  row = await module.cancel(params.guid)
  payload = SystemWorkflowRunItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_rollback_run_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunRollbackRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  row = await module.rollback(params.guid)
  payload = SystemWorkflowRunItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_resume_run_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunResumeRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  row = await module.resume(params.guid)
  payload = SystemWorkflowRunItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_retry_run_action_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunRetryActionRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  row = await module.retry_action(params.run_action_guid)
  payload = SystemWorkflowRunActionItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_list_run_actions_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunActionListRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  run = await module.get(params.run_guid)
  if not run:
    raise HTTPException(status_code=404, detail="Workflow run not found")
  rows = await module.list_run_actions(run["recid"])
  payload = SystemWorkflowRunActionList1(actions=[SystemWorkflowRunActionItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_workflows_scan_stalls_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowScanStallsRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  result = await module.scan_stalls(params.payload)
  payload = SystemWorkflowScanStallsResponse1(**result)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
