from fastapi import APIRouter, Request
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest, RPCResponse

router = APIRouter()

@router.post("")
@router.post("/")
async def post_root(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  return await handle_rpc_request(rpc_request, request)
