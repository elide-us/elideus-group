from fastapi import Request, HTTPException
from rpc.admin.vars.handler import handle_vars_request
from rpc.admin.links.handler import handle_links_request

async def handle_admin_request(urn: list[str], request: Request):
  match urn:
    case ["vars", *rest]:
      return await handle_vars_request(rest, request)
    case ["links", *rest]:
      return await handle_links_request(rest, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
