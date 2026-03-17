from fastapi import Request

from queryregistry.finance.vendors import (
  delete_vendor_request,
  list_vendors_request,
  upsert_vendor_request,
)
from queryregistry.finance.vendors.models import (
  DeleteVendorParams,
  ListVendorsParams,
  UpsertVendorParams,
)
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
  FinanceVendorDelete1,
  FinanceVendorDeleteResult1,
  FinanceVendorItem1,
  FinanceVendorList1,
  FinanceVendorUpsert1,
)


async def finance_vendors_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(list_vendors_request(ListVendorsParams()))
  payload = FinanceVendorList1(vendors=[FinanceVendorItem1(**dict(row)) for row in (result.rows or [])])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_vendors_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceVendorUpsert1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(upsert_vendor_request(UpsertVendorParams(**input_payload.model_dump())))
  row = dict(result.rows[0]) if result.rows else input_payload.model_dump()
  payload = FinanceVendorItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_vendors_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceVendorDelete1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(delete_vendor_request(DeleteVendorParams(recid=input_payload.recid)))
  payload = FinanceVendorDeleteResult1(recid=input_payload.recid, deleted=True)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
