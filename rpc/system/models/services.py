from fastapi import Request

from queryregistry.system.models_registry import (
  delete_model_request,
  list_models_request,
  upsert_model_request,
)
from queryregistry.system.models_registry.models import DeleteModelParams, UpsertModelParams
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
  API_PROVIDERS,
  SystemModelsDeleteModel1,
  SystemModelsList1,
  SystemModelsModelItem1,
  SystemModelsUpsertModel1,
)


async def system_models_get_models_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(list_models_request())
  models = []
  for row in res.rows or []:
    models.append(SystemModelsModelItem1(
      recid=row.get("recid", 0),
      name=row.get("element_name", ""),
      api_provider=row.get("element_api_provider", "openai"),
      is_active=bool(row.get("element_is_active", True)),
    ))
  payload = SystemModelsList1(models=models, api_providers=API_PROVIDERS)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def system_models_upsert_model_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  rpc_payload = SystemModelsUpsertModel1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(upsert_model_request(UpsertModelParams(
    recid=rpc_payload.recid,
    name=rpc_payload.name,
    api_provider=rpc_payload.api_provider,
    is_active=rpc_payload.is_active,
  )))
  return RPCResponse(op=rpc_request.op, payload=rpc_payload.model_dump(), version=rpc_request.version)


async def system_models_delete_model_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  rpc_payload = SystemModelsDeleteModel1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(delete_model_request(DeleteModelParams(
    recid=rpc_payload.recid,
    name=rpc_payload.name,
  )))
  return RPCResponse(op=rpc_request.op, payload=rpc_payload.model_dump(), version=rpc_request.version)
