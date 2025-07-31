from fastapi import Request
from rpc.helpers import get_rpcrequest_from_request
from . import services


def _wrap(func):
  async def wrapped(request: Request):
    rpc_request, _ = await get_rpcrequest_from_request(request)
    return await func(rpc_request, request)
  return wrapped

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): services.get_users_v1,
  ("get_roles", "1"): _wrap(services.get_user_roles_v1),
  ("set_roles", "1"): _wrap(services.set_user_roles_v1),
  ("list_roles", "1"): services.list_available_roles_v1,
  ("get_profile", "1"): _wrap(services.get_user_profile_v1),
  ("set_credits", "1"): _wrap(services.set_user_credits_v1),
  ("set_display_name", "1"): _wrap(services.set_user_display_name_v1),
  ("enable_storage", "1"): _wrap(services.enable_user_storage_v1),
  ("list", "2"): services.get_users_v2,
  ("get_roles", "2"): _wrap(services.get_user_roles_v2),
  ("set_roles", "2"): _wrap(services.set_user_roles_v2),
  ("list_roles", "2"): services.list_available_roles_v2,
  ("get_profile", "2"): _wrap(services.get_user_profile_v2),
  ("set_credits", "2"): _wrap(services.set_user_credits_v2),
  ("set_display_name", "2"): _wrap(services.set_user_display_name_v2),
  ("enable_storage", "2"): _wrap(services.enable_user_storage_v2),
}
