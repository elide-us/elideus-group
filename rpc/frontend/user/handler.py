from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.frontend.user import services

async def handle_user_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ['get_profile_data', '1']:
      return await services.get_profile_data_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC operation')
