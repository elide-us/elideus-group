from fastapi import Request
from server.models import RPCResponse
from rpc.account.user import services as account_user_services

async def support_users_get_profile_v1(request: Request) -> RPCResponse:
  return await account_user_services.account_user_get_profile_v1(request)

async def support_users_set_credits_v1(request: Request) -> RPCResponse:
  return await account_user_services.account_user_set_credits_v1(request)

async def support_users_reset_display_v1(request: Request) -> RPCResponse:
  return await account_user_services.account_user_reset_display_v1(request)

async def support_users_enable_storage_v1(request: Request) -> RPCResponse:
  return await account_user_services.account_user_enable_storage_v1(request)

async def support_users_check_storage_v1(request: Request) -> RPCResponse:
  return await account_user_services.account_user_check_storage_v1(request)
