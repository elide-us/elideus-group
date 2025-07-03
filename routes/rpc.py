from fastapi import APIRouter, Request, HTTPException
from routes.admin.rpc import handle_admin_request
from models.rpc import RPCRequest, RPCResponse

router = APIRouter()

@router.post("/")
async def handle_rpc_request(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  parts = rpc_request.op.split(":")

  if parts[:1] != ["urn"]:
    raise HTTPException(400, "Invalid URN prefix")

  match parts[1:]:
    case ["admin", *rest]:
      return await handle_admin_request(rest, request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC domain")