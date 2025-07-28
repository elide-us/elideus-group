from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.account.users import services

async def handle_users_request(parts: list[str], rpc_request: RPCRequest | None, request: Request) -> RPCResponse:
  match parts:
    case ["list", "1"]:
      return await services.get_users_v1(request)
    case ["list", "2"]:
      return await services.get_users_v2(request)
    case ["get_roles", "1"]:
      return await services.get_user_roles_v1(rpc_request, request)
    case ["get_roles", "2"]:
      return await services.get_user_roles_v2(rpc_request, request)
    case ["set_roles", "1"]:
      return await services.set_user_roles_v1(rpc_request, request)
    case ["set_roles", "2"]:
      return await services.set_user_roles_v2(rpc_request, request)
    case ["list_roles", "1"]:
      return await services.list_available_roles_v1(request)
    case ["list_roles", "2"]:
      return await services.list_available_roles_v2(request)
    case ["get_profile", "1"]:
      return await services.get_user_profile_v1(rpc_request, request)
    case ["get_profile", "2"]:
      return await services.get_user_profile_v2(rpc_request, request)
    case ["set_credits", "1"]:
      return await services.set_user_credits_v1(rpc_request, request)
    case ["set_credits", "2"]:
      return await services.set_user_credits_v2(rpc_request, request)
    case ["set_display_name", "1"]:
      return await services.set_user_display_name_v1(rpc_request, request)
    case ["set_display_name", "2"]:
      return await services.set_user_display_name_v2(rpc_request, request)
    case ["enable_storage", "1"]:
      return await services.enable_user_storage_v1(rpc_request, request)
    case ["enable_storage", "2"]:
      return await services.enable_user_storage_v2(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC operation')
