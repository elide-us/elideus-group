from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinanceVendorDelete1,
  FinanceVendorDeleteResult1,
  FinanceVendorItem1,
  FinanceVendorList1,
  FinanceVendorUpsert1,
)


async def finance_vendors_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_vendors()
  payload = FinanceVendorList1(vendors=[FinanceVendorItem1(**dict(row)) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_vendors_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceVendorUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.upsert_vendor(input_payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinanceVendorItem1(**dict(row))
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_vendors_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceVendorDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_vendor(input_payload.recid)
  payload = FinanceVendorDeleteResult1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
