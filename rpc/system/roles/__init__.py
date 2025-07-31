from fastapi import Request
from rpc.helpers import get_rpcrequest_from_request
from . import services


def _wrap(func):
  async def wrapped(request: Request):
    rpc_request, _ = await get_rpcrequest_from_request(request)
    return await func(rpc_request, request)
  return wrapped

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): services.list_roles_v1,
  ("set", "1"): _wrap(services.set_role_v1),
  ("delete", "1"): _wrap(services.delete_role_v1),
  ("get_members", "1"): _wrap(services.get_role_members_v1),
  ("add_member", "1"): _wrap(services.add_role_member_v1),
  ("remove_member", "1"): _wrap(services.remove_role_member_v1),
  ("list", "2"): services.list_roles_v2,
  ("set", "2"): _wrap(services.set_role_v2),
  ("delete", "2"): _wrap(services.delete_role_v2),
  ("get_members", "2"): _wrap(services.get_role_members_v2),
  ("add_member", "2"): _wrap(services.add_role_member_v2),
  ("remove_member", "2"): _wrap(services.remove_role_member_v2),
}
