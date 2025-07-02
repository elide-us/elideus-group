from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

class RPCRequest(BaseModel):
  op: str
  payload: dict[str, Any]
  version: int

router = APIRouter()

@router.get("/")
async def handle_rpc_request(rpcrequest: RPCRequest):
  return