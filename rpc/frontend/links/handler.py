from fastapi import Request, HTTPException
from rpc.frontend.links import services
from rpc.models import RPCResponse

async def handle_links_request(parts: list[str], request: Request) -> RPCResponse:
  match parts:
    case ["get_home", "1"]:
      return await services.get_home_v1(request)
    case ["get_routes", "1"]:
      return await services.get_routes_v1(request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")

