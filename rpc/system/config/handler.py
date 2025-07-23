from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.system.config import services

async def handle_config_request(parts: list[str], rpc_request: RPCRequest | None, request: Request) -> RPCResponse:
  match parts:
    case ["list", "1"]:
      return await services.list_config_v1(request)
    case ["set", "1"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.set_config_v1(rpc_request, request)
    case ["delete", "1"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.delete_config_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC operation')
