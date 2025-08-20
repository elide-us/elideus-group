from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import UsersProvidersSetProvider1


async def users_providers_set_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersSetProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {
    "guid": auth_ctx.user_guid,
    "provider": payload.provider,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_providers_link_provider_v1(request: Request):
  raise NotImplementedError("urn:users:providers:link_provider:1")

async def users_providers_unlink_provider_v1(request: Request):
  raise NotImplementedError("urn:users:providers:unlink_provider:1")

async def users_providers_get_by_provider_identifier_v1(request: Request):
  raise NotImplementedError("urn:users:providers:get_by_provider_identifier:1")

async def users_providers_create_from_provider_v1(request: Request):
  raise NotImplementedError("urn:users:providers:create_from_provider:1")

