from fastapi import Request, HTTPException
import logging
from rpc.auth.microsoft.handler import handle_ms_request
from rpc.models import RPCRequest, RPCResponse

async def handle_auth_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  logging.info(
    "handle_auth_request parts=%s op=%s payload=%s",
    parts,
    rpc_request.op,
    rpc_request.payload,
  )
  match parts:
    case ["microsoft", *rest]:
      return await handle_ms_request(rest, rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
