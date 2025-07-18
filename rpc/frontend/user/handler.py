from fastapi import Request, HTTPException
from rpc.frontend.user import services
from rpc.models import RPCRequest, RPCResponse

async def handle_user_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ["set_display_name", "1"]:
      return await services.set_display_name_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")
