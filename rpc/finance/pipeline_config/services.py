from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinancePipelineConfigDelete1,
  FinancePipelineConfigDeleteResult1,
  FinancePipelineConfigFilter1,
  FinancePipelineConfigGet1,
  FinancePipelineConfigItem1,
  FinancePipelineConfigList1,
  FinancePipelineConfigUpsert1,
)


async def finance_pipeline_config_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinancePipelineConfigFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_pipeline_configs(payload.element_pipeline)
  response_payload = FinancePipelineConfigList1(
    configs=[FinancePipelineConfigItem1(**dict(row)) for row in rows]
  )
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_pipeline_config_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinancePipelineConfigGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_pipeline_config_record(payload.element_pipeline, payload.element_key)
  if not row:
    raise HTTPException(status_code=404, detail="Pipeline config not found")
  response_payload = FinancePipelineConfigItem1(**dict(row))
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_pipeline_config_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinancePipelineConfigUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.upsert_pipeline_config(payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = FinancePipelineConfigItem1(**dict(row))
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_pipeline_config_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinancePipelineConfigDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_pipeline_config(payload.recid)
  response_payload = FinancePipelineConfigDeleteResult1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)
