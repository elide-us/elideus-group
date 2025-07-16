from fastapi import Request, HTTPException
from rpc.auth.microsoft import services
from rpc.models import RPCRequest, RPCResponse

async def handle_ms_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ["user_login", "1"]:
      return await services.user_login_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")

