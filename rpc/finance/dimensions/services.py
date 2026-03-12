from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinanceDimensionsDelete1,
  FinanceDimensionsGet1,
  FinanceDimensionsItem1,
  FinanceDimensionsList1,
  FinanceDimensionsListByName1,
  FinanceDimensionsUpsert1,
)


async def finance_dimensions_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_dimensions()
  payload = FinanceDimensionsList1(dimensions=[FinanceDimensionsItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_dimensions_list_by_name_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceDimensionsListByName1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_dimensions_by_name(input_payload.name)
  payload = FinanceDimensionsList1(dimensions=[FinanceDimensionsItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_dimensions_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceDimensionsGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_dimension(input_payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Dimension not found")
  payload = FinanceDimensionsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_dimensions_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceDimensionsUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.upsert_dimension(input_payload.model_dump())
  payload = FinanceDimensionsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_dimensions_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceDimensionsDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_dimension(input_payload.recid)
  payload = FinanceDimensionsDelete1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
