from fastapi import Request
from rpc.helpers import get_rpcrequest_from_request
from . import services

async def refresh_v1(request: Request):
  rpc_request, _ = await get_rpcrequest_from_request(request)
  return await services.refresh_v1(rpc_request, request)

async def invalidate_v1(request: Request):
  rpc_request, _ = await get_rpcrequest_from_request(request)
  return await services.invalidate_v1(rpc_request, request)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("refresh", "1"): refresh_v1,
  ("invalidate", "1"): invalidate_v1,
}
