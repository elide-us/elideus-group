from fastapi import Request, HTTPException
from rpc.system.users.handler import handle_users_request
from rpc.system.roles.handler import handle_roles_request
from rpc.system.routes.handler import handle_routes_request
from rpc.system.config.handler import handle_config_request
from rpc.models import RPCRequest, RPCResponse

async def handle_system_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ["users", *rest]:
      return await handle_users_request(rest, rpc_request, request)
    case ["roles", *rest]:
      return await handle_roles_request(rest, rpc_request, request)
    case ["routes", *rest]:
      return await handle_routes_request(rest, rpc_request, request)
    case ["config", *rest]:
      return await handle_config_request(rest, rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
