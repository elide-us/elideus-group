from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.models_registry_module import ModelsRegistryModule

from .models import (
  SystemModelsDeleteModel1,
  SystemModelsList1,
  SystemModelsModelItem1,
  SystemModelsUpsertModel1,
)


async def system_models_get_models_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module: ModelsRegistryModule = request.app.state.models_registry
  await module.on_ready()
  rows = await module.list_models_registry()
  models = []
  for row in rows:
    models.append(SystemModelsModelItem1(
      recid=row.get("recid", 0),
      name=row.get("element_name", ""),
      api_provider=row.get("element_api_provider", "openai"),
      is_active=bool(row.get("element_is_active", True)),
    ))
  api_providers = await module.get_api_providers()
  payload = SystemModelsList1(models=models, api_providers=api_providers)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_models_upsert_model_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  rpc_payload = SystemModelsUpsertModel1(**(rpc_request.payload or {}))
  module: ModelsRegistryModule = request.app.state.models_registry
  await module.on_ready()
  await module.upsert_model_registry(rpc_payload.model_dump())
  return RPCResponse(op=rpc_request.op, payload=rpc_payload.model_dump(), version=rpc_request.version)


async def system_models_delete_model_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  rpc_payload = SystemModelsDeleteModel1(**(rpc_request.payload or {}))
  module: ModelsRegistryModule = request.app.state.models_registry
  await module.on_ready()
  await module.delete_model_registry(recid=rpc_payload.recid, name=rpc_payload.name)
  return RPCResponse(op=rpc_request.op, payload=rpc_payload.model_dump(), version=rpc_request.version)
