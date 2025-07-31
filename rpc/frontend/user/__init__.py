from fastapi import Request
from rpc.helpers import get_rpcrequest_from_request
from . import services


def _wrap(func):
  async def wrapped(request: Request):
    rpc_request, _ = await get_rpcrequest_from_request(request)
    return await func(rpc_request, request)
  return wrapped

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_profile_data", "1"): _wrap(services.get_profile_data_v1),
  ("set_display_name", "1"): _wrap(services.set_display_name_v1),
}
