from fastapi import Request, HTTPException
from rpc.admin.roles import services
from rpc.models import RPCRequest, RPCResponse

async def handle_roles_request(parts: list[str], rpc_request: RPCRequest | None, request: Request) -> RPCResponse:
  match parts:
    case ["list", "1"]:
      return await services.list_roles_v1(request)
    case ["set", "1"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.set_role_v1(rpc_request, request)
    case ["delete", "1"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.delete_role_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC operation')

