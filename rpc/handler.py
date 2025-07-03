from fastapi import Request, HTTPException
from rpc.admin.handler import handle_admin_request
from rpc.models import RPCRequest, RPCResponse

async def handle_rpc_request(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  parts = rpc_request.op.split(":")

  if parts[:1] != ["urn"]:
    raise HTTPException(400, "Invalid URN prefix")

  match parts[1:]:
    case ["admin", *rest]:
      return await handle_admin_request(rest, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC domain")