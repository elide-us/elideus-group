from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinanceLedgersCreate1,
  FinanceLedgersDelete1,
  FinanceLedgersGet1,
  FinanceLedgersItem1,
  FinanceLedgersList1,
  FinanceLedgersUpdate1,
)


async def finance_ledgers_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_ledgers()
  payload = FinanceLedgersList1(ledgers=[FinanceLedgersItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_ledgers_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceLedgersGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_ledger(input_payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Ledger not found")
  payload = FinanceLedgersItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_ledgers_create_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceLedgersCreate1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.create_ledger(input_payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinanceLedgersItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_ledgers_update_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceLedgersUpdate1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.update_ledger(input_payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinanceLedgersItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_ledgers_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceLedgersDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.delete_ledger(input_payload.recid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinanceLedgersItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
