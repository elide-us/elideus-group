from fastapi import Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.storage_module import StorageModule
from .models import SystemStorageStats1


async def system_storage_get_stats_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module: StorageModule = request.app.state.storage
  reindex = bool((rpc_request.payload or {}).get("reindex"))
  stats = await module.get_storage_stats(reindex=reindex)
  payload = SystemStorageStats1(**stats)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

