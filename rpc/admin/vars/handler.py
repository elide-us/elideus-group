from typing import List
from fastapi import Request, HTTPException
from rpc.admin.vars.services import get_version_v1, get_hostname_v1

async def handle_vars_request(urn: List, request: Request):
  match urn[1:]:
    case ["get_version", "1"]:
      return await get_version_v1(request)
    case ["get_hostname", "1"]:
      return await get_hostname_v1(request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")
