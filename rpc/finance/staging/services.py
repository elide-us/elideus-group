from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  StagingApprove1,
  StagingApproveResult1,
  StagingDeleteImport1,
  StagingDeleteResult1,
  StagingImport1,
  StagingImportInvoices1,
  StagingImportInvoicesResult1,
  StagingImportItem1,
  StagingImportList1,
  StagingImportResult1,
  StagingLineItem1,
  StagingLineItemList1,
  StagingListDetails1,
  StagingListImports1,
  StagingPromote1,
  StagingPromoteResult1,
  StagingReject1,
  StagingRejectResult1,
)


async def finance_staging_import_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingImport1(**(rpc_request.payload or {}))
  module = request.app.state.billing_import
  await module.on_ready()
  result: StagingImportInvoicesResult1 = await module.run_import(
    "azure_cost_details",
    period_start=payload.period_start,
    period_end=payload.period_end,
    metric=payload.metric,
  )
  response_payload = StagingImportResult1(**result)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_import_invoices_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingImportInvoices1(**(rpc_request.payload or {}))
  module = request.app.state.billing_import
  await module.on_ready()
  result: StagingImportInvoicesResult1 = await module.run_import(
    "azure_invoices",
    period_month=payload.period_month,
    billing_account=payload.billing_account,
  )
  response_payload = StagingImportInvoicesResult1(**result)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_list_imports_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingListImports1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_imports(payload.status)
  response_payload = StagingImportList1(imports=[StagingImportItem1(**dict(row)) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_list_details_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingListDetails1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_cost_details_by_import(payload.imports_recid)
  return RPCResponse(op=rpc_request.op, payload=rows, version=rpc_request.version)


async def finance_staging_delete_import_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingDeleteImport1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_import(payload.imports_recid)
  response_payload = StagingDeleteResult1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_approve_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingApprove1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    await module.approve_import(payload.imports_recid, auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = StagingApproveResult1(imports_recid=payload.imports_recid, approved=True)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_reject_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingReject1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    await module.reject_import(payload.imports_recid, auth_ctx.user_guid, payload.reason)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = StagingRejectResult1(imports_recid=payload.imports_recid, rejected=True)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_promote_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingPromote1(**(rpc_request.payload or {}))
  module = request.app.state.workflow
  await module.on_ready()
  run = await module.submit(
    workflow_name="billing_import",
    payload={
      "imports_recid": payload.imports_recid,
      "ledgers_recid": payload.ledgers_recid,
    },
    source_type="rpc",
    source_id=str(payload.imports_recid),
    created_by=auth_ctx.user_guid,
    timeout_seconds=600,
  )
  result = StagingPromoteResult1(task_guid=run["guid"])
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def finance_staging_list_line_items_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingListDetails1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_line_items_by_import(payload.imports_recid)
  response_payload = StagingLineItemList1(
    line_items=[StagingLineItem1(**dict(row)) for row in rows],
  )
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)
