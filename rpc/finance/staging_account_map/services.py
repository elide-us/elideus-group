from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinanceStagingAccountMapDelete1,
  FinanceStagingAccountMapDeleteResult1,
  FinanceStagingAccountMapItem1,
  FinanceStagingAccountMapList1,
  FinanceStagingAccountMapUpsert1,
)


async def finance_staging_account_map_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_account_mappings()
  payload = FinanceStagingAccountMapList1(
    mappings=[FinanceStagingAccountMapItem1(**dict(row)) for row in rows]
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_staging_account_map_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceStagingAccountMapUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.upsert_account_mapping(input_payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinanceStagingAccountMapItem1(**dict(row))
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_staging_account_map_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceStagingAccountMapDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_account_mapping(input_payload.recid)
  payload = FinanceStagingAccountMapDeleteResult1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
