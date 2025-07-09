from fastapi import Request, HTTPException
from rpc.admin.links import services

async def handle_links_request(urn: list[str], request: Request):
  match urn:
    case ["get_home", "1"]:
      return await services.get_home_v1(request)
    case ["get_routes", "1"]:
      return await services.get_routes_v1(request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")
