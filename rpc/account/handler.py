from fastapi import Request, HTTPException
from rpc.account.users.handler import handle_users_request
from rpc.account.roles.handler import handle_roles_request
from rpc.models import RPCRequest, RPCResponse

async def handle_account_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ["users", *rest]:
      return await handle_users_request(rest, rpc_request, request)
    case ["roles", *rest]:
      return await handle_roles_request(rest, rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
