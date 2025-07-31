from fastapi import Request
from rpc.helpers import get_rpcrequest_from_request
from . import services

async def user_login_v1(request: Request):
  rpc_request, _ = await get_rpcrequest_from_request(request)
  return await services.user_login_v1(rpc_request, request)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("user_login", "1"): user_login_v1,
}
