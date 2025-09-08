from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import StorageProvisionStatus1


async def storage_provision_create_user_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  return RPCResponse(
    op=rpc_request.op,
    payload=None,
    version=rpc_request.version,
  )


async def storage_provision_check_user_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  payload = StorageProvisionStatus1(exists=False)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
