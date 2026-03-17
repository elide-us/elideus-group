from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinanceNumbersDelete1,
  FinanceNumbersItem1,
  FinanceNumbersList1,
  FinanceNumbersNextNumber1,
  FinanceNumbersShift1,
  FinanceNumbersShiftResult1,
  FinanceNumbersUpsert1,
)


async def finance_numbers_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_numbers()
  payload = FinanceNumbersList1(numbers=[FinanceNumbersItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_numbers_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceNumbersDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_number(input_payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Number sequence not found")
  payload = FinanceNumbersItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_numbers_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceNumbersUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.upsert_number(input_payload.model_dump())
  payload = FinanceNumbersItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_numbers_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceNumbersDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_number(input_payload.recid)
  payload = FinanceNumbersDelete1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_numbers_next_number_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceNumbersNextNumber1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.next_number(input_payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Number sequence not found")
  payload = FinanceNumbersItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_numbers_shift_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceNumbersShift1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.shift_sequence(input_payload.model_dump())
  payload = FinanceNumbersShiftResult1(
    closed_sequence=FinanceNumbersItem1(**row["closed_sequence"]) if row.get("closed_sequence") else None,
    new_sequence=FinanceNumbersItem1(**row["new_sequence"]),
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
