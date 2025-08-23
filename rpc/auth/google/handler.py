from fastapi import Request, HTTPException
import logging
from rpc.auth.google import services
from rpc.models import RPCRequest, RPCResponse

async def handle_google_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  logging.debug(
    "handle_google_request parts=%s op=%s payload=%s",
    parts,
    rpc_request.op,
    rpc_request.payload,
  )
  match parts:
    case ["user_login", "1"]:
      return await services.user_login_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")
