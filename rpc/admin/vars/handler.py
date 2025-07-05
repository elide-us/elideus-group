from fastapi import Request, HTTPException
from rpc.admin.vars.services import get_version_v1, get_hostname_v1, get_repo_v1

async def handle_vars_request(urn: list[str], request: Request):
  match urn:
    case ["get_version", "1"]:
      return await get_version_v1(request)
    case ["get_hostname", "1"]:
      return await get_hostname_v1(request)
    case ["get_repo", "1"]:
      return await get_repo_v1(request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")

