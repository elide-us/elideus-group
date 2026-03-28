from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.workflow_module import WorkflowModule

from .models import (
  SystemWorkflowDetail1,
  SystemWorkflowGetRequest1,
  SystemWorkflowItem1,
  SystemWorkflowList1,
  SystemWorkflowListRequest1,
  SystemWorkflowRunCancelRequest1,
  SystemWorkflowRunGetRequest1,
  SystemWorkflowRunItem1,
  SystemWorkflowRunList1,
  SystemWorkflowRunListRequest1,
  SystemWorkflowRunRollbackRequest1,
  SystemWorkflowRunStepItem1,
  SystemWorkflowRunStepList1,
  SystemWorkflowRunStepListRequest1,
  SystemWorkflowRunSubmitRequest1,
  SystemWorkflowStepItem1,
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
  steps = await module.list_steps(workflow["guid"])
  payload = SystemWorkflowDetail1(
    guid=workflow["guid"],
    name=workflow["name"],
    description=workflow.get("description"),
    version=workflow["version"],
    status=workflow["status"],
    steps=[SystemWorkflowStepItem1(**step) for step in steps],
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
    source_type=params.source_type,
    source_id=params.source_id,
    created_by=auth_ctx.user_guid,
    timeout_seconds=params.timeout_seconds,
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


async def system_workflows_list_run_steps_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemWorkflowRunStepListRequest1(**(rpc_request.payload or {}))
  module: WorkflowModule = request.app.state.workflow
  await module.on_ready()
  run = await module.get(params.run_guid)
  if not run:
    raise HTTPException(status_code=404, detail="Workflow run not found")
  rows = await module.list_run_steps(run["recid"])
  payload = SystemWorkflowRunStepList1(steps=[SystemWorkflowRunStepItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
