from fastapi import Request

from queryregistry.finance.staging import (
  delete_import_request,
  list_cost_details_by_import_request,
  list_imports_request,
)
from queryregistry.finance.staging.models import (
  DeleteImportParams,
  ListCostDetailsByImportParams,
  ListImportsParams,
)
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
  StagingDeleteImport1,
  StagingDeleteResult1,
  StagingImport1,
  StagingImportItem1,
  StagingImportList1,
  StagingImportResult1,
  StagingListDetails1,
)


async def finance_staging_import_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = StagingImport1(**(rpc_request.payload or {}))
  module = request.app.state.azure_billing_import
  await module.on_ready()
  result = await module.import_cost_details(
    payload.period_start,
    payload.period_end,
    payload.metric,
  )
  response_payload = StagingImportResult1(**result)
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
