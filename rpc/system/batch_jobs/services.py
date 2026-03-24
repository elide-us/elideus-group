from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  BatchJobDelete1,
  BatchJobGet1,
  BatchJobHistoryItem1,
  BatchJobHistoryList1,
  BatchJobItem1,
  BatchJobList1,
  BatchJobListHistory1,
  BatchJobRunNow1,
  BatchJobUpsert1,
)


async def system_batch_jobs_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.batch_job
  await module.on_ready()
  rows = await module.list_jobs()
  payload = BatchJobList1(jobs=[BatchJobItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_batch_jobs_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = BatchJobGet1(**(rpc_request.payload or {}))
  module = request.app.state.batch_job
  await module.on_ready()
  row = await module.get_job(input_payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Batch job not found")
  payload = BatchJobItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_batch_jobs_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = BatchJobUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.batch_job
  await module.on_ready()
  row = await module.upsert_job(input_payload.model_dump())
  payload = BatchJobItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_batch_jobs_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = BatchJobDelete1(**(rpc_request.payload or {}))
  module = request.app.state.batch_job
  await module.on_ready()
  row = await module.delete_job(input_payload.recid)
  payload = BatchJobDelete1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_batch_jobs_list_history_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = BatchJobListHistory1(**(rpc_request.payload or {}))
  module = request.app.state.batch_job
  await module.on_ready()
  rows = await module.list_history(input_payload.jobs_recid)
  payload = BatchJobHistoryList1(history=[BatchJobHistoryItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_batch_jobs_run_now_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = BatchJobRunNow1(**(rpc_request.payload or {}))
  module = request.app.state.batch_job
  await module.on_ready()
  row = await module.run_now(input_payload.recid)
  payload = BatchJobItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
