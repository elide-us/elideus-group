from fastapi import APIRouter, Request
from rpc.handler import handle_rpc_request
from rpc.models import RPCResponse

router = APIRouter()

@router.post("")
@router.post("/")
async def post_root(request: Request) -> RPCResponse:
  return await handle_rpc_request(request)
