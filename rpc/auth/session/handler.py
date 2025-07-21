from fastapi import Request, HTTPException
import logging
from rpc.auth.session import services
from rpc.models import RPCRequest, RPCResponse

async def handle_session_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  logging.debug("handle_session_request parts=%s", parts)
  match parts:
    case ["refresh", "1"]:
      return await services.refresh_v1(rpc_request, request)
    case ["invalidate", "1"]:
      return await services.invalidate_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")
