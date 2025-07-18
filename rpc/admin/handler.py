from fastapi import Request, HTTPException
from rpc.admin.vars.handler import handle_vars_request
from rpc.admin.links.handler import handle_links_request
from rpc.models import RPCResponse

async def handle_admin_request(parts: list[str], request: Request) -> RPCResponse:
  match parts:
    case ["vars", *rest]:
      return await handle_vars_request(rest, request)
    case ["links", *rest]:
      return await handle_links_request(rest, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
