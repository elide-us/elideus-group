from fastapi import Request
from rpc.helpers import get_rpcrequest_from_request
from . import services


def _wrap(func):
  async def wrapped(request: Request):
    rpc_request, _ = await get_rpcrequest_from_request(request)
    return await func(rpc_request, request)
  return wrapped

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): services.list_routes_v1,
  ("set", "1"): _wrap(services.set_route_v1),
  ("delete", "1"): _wrap(services.delete_route_v1),
  ("list", "2"): services.list_routes_v2,
  ("set", "2"): _wrap(services.set_route_v2),
  ("delete", "2"): _wrap(services.delete_route_v2),
}
