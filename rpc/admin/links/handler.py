from fastapi import Request, HTTPException
import rpc.admin.links.services as services

async def handle_links_request(urn: list[str], request: Request):
  match urn:
    case ["get_home", "1"]:
      return await services.get_home_v1(request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")
