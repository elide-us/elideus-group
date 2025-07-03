from typing import List
from fastapi import Request, HTTPException
from rpc.admin.vars.handler import handle_vars_request

async def handle_admin_request(urn: List, request: Request):
  match urn[1:]:
    case ["env", *rest]:
      return await handle_vars_request(rest, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
