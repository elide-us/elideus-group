from fastapi import Request, HTTPException
from rpc.auth.microsoft.handler import handle_ms_request
from rpc.models import RPCRequest

async def handle_auth_request(urn: list[str], rpc_request: RPCRequest, request: Request):
  match urn:
    case ["microsoft", *rest]:
      return await handle_ms_request(rest, rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
