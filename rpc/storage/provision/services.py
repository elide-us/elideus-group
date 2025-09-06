from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.storage_module import StorageModule

from .models import StorageProvisionStatus1


async def storage_provision_create_user_v1(request: Request) -> RPCResponse:
  rpc_request, auth_ctx, _ = await unbox_request(request)
  storage: StorageModule = request.app.state.storage
  await storage.ensure_user_folder(auth_ctx.user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=None,
    version=rpc_request.version,
  )


async def storage_provision_check_user_v1(request: Request) -> RPCResponse:
  rpc_request, auth_ctx, _ = await unbox_request(request)
  storage: StorageModule = request.app.state.storage
  exists = await storage.user_folder_exists(auth_ctx.user_guid)
  payload = StorageProvisionStatus1(exists=exists)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
