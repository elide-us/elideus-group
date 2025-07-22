from fastapi import Request, HTTPException
from rpc.admin.vars.handler import handle_vars_request
from rpc.admin.links.handler import handle_links_request
from rpc.admin.users.handler import handle_users_request
from rpc.admin.roles.handler import handle_roles_request
from rpc.admin.routes.handler import handle_routes_request
from rpc.admin.config.handler import handle_config_request
from rpc.models import RPCRequest, RPCResponse

async def handle_admin_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ["vars", *rest]:
      return await handle_vars_request(rest, request)
    case ["links", *rest]:
      return await handle_links_request(rest, request)
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
