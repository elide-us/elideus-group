from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  SystemTaskCancelRequest1,
  SystemTaskEventsList1,
  SystemTaskEventsRequest1,
  SystemTaskEventItem1,
  SystemTaskGetRequest1,
  SystemTaskItem1,
  SystemTaskList1,
  SystemTaskListRequest1,
  SystemTaskRetryRequest1,
  SystemTaskSubmitRequest1,
)


async def system_tasks_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemTaskListRequest1(**(rpc_request.payload or {}))
  module = request.app.state.async_task
  await module.on_ready()
  rows = await module.list_tasks(
    status=params.status,
    handler_type=params.handler_type,
    handler_name=params.handler_name,
  )
  payload = SystemTaskList1(tasks=[SystemTaskItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_tasks_get_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemTaskGetRequest1(**(rpc_request.payload or {}))
  module = request.app.state.async_task
  await module.on_ready()
  row = await module.get_task(params.guid)
  if not row:
    raise HTTPException(status_code=404, detail="Task not found")
  payload = SystemTaskItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_tasks_submit_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = SystemTaskSubmitRequest1(**(rpc_request.payload or {}))
  module = request.app.state.async_task
  await module.on_ready()
  row = await module.submit_task(
    handler_name=params.handler_name,
    payload=params.payload,
    source_type=params.source_type,
    source_id=params.source_id,
    created_by=auth_ctx.user_guid,
    timeout_seconds=params.timeout_seconds,
    poll_interval_seconds=params.poll_interval_seconds,
    max_retries=params.max_retries,
  )
  payload = SystemTaskItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_tasks_cancel_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemTaskCancelRequest1(**(rpc_request.payload or {}))
  module = request.app.state.async_task
  await module.on_ready()
  row = await module.cancel_task(params.guid)
  payload = SystemTaskItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_tasks_retry_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemTaskRetryRequest1(**(rpc_request.payload or {}))
  module = request.app.state.async_task
  await module.on_ready()
  row = await module.retry_task(params.guid)
  payload = SystemTaskItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_tasks_events_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = SystemTaskEventsRequest1(**(rpc_request.payload or {}))
  module = request.app.state.async_task
  await module.on_ready()
  rows = await module.list_task_events(params.guid)
  payload = SystemTaskEventsList1(events=[SystemTaskEventItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
