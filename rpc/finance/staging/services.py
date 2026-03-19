from fastapi import Request

from queryregistry.finance.staging import (
  delete_import_request,
  list_cost_details_by_import_request,
  list_imports_request,
)
from queryregistry.finance.staging_line_items import list_line_items_by_import_request
from queryregistry.finance.staging.models import (
  DeleteImportParams,
  ListCostDetailsByImportParams,
  ListImportsParams,
)
from queryregistry.finance.staging_line_items.models import ListLineItemsByImportParams
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
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
  StagingPromote1,
  StagingPromoteResult1,
)


async def finance_staging_import_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingImport1(**(rpc_request.payload or {}))
  module = request.app.state.billing_import
  await module.on_ready()
  result = await module.run_import(
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
  result = await module.run_import(
    "azure_invoices",
    period_month=payload.period_month,
    billing_account=payload.billing_account,
  )
  response_payload = StagingImportInvoicesResult1(**result)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_list_imports_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(list_imports_request(ListImportsParams()))
  imports = [StagingImportItem1(**row) for row in (result.rows or [])]
  response_payload = StagingImportList1(imports=imports)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_list_details_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingListDetails1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(
    list_cost_details_by_import_request(
      ListCostDetailsByImportParams(imports_recid=payload.imports_recid),
    ),
  )
  return RPCResponse(op=rpc_request.op, payload=(result.rows or []), version=rpc_request.version)


async def finance_staging_delete_import_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingDeleteImport1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(delete_import_request(DeleteImportParams(imports_recid=payload.imports_recid)))
  response_payload = StagingDeleteResult1(imports_recid=payload.imports_recid, deleted=True)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_staging_promote_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingPromote1(**(rpc_request.payload or {}))
  module = request.app.state.async_task
  await module.on_ready()
  task = await module.submit_task(
    handler_name="finance.billing.import_pipeline",
    payload={
      "imports_recid": payload.imports_recid,
      "ledgers_recid": payload.ledgers_recid,
    },
    source_type="rpc",
    source_id=str(payload.imports_recid),
    created_by=auth_ctx.user_guid,
    timeout_seconds=600,
    poll_interval_seconds=None,
    max_retries=0,
  )
  result = StagingPromoteResult1(task_guid=task["guid"])
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def finance_staging_list_line_items_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingListDetails1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(
    list_line_items_by_import_request(
      ListLineItemsByImportParams(imports_recid=payload.imports_recid),
    ),
  )
  response_payload = StagingLineItemList1(
    line_items=[StagingLineItem1(**dict(row)) for row in (result.rows or [])],
  )
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)
