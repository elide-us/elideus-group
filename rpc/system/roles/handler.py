from fastapi import Request, HTTPException
from rpc.system.roles import services
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
    case ["get_members", "1"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.get_role_members_v1(rpc_request, request)
    case ["add_member", "1"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.add_role_member_v1(rpc_request, request)
    case ["remove_member", "1"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.remove_role_member_v1(rpc_request, request)
    case ["list", "2"]:
      return await services.list_roles_v2(request)
    case ["set", "2"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.set_role_v2(rpc_request, request)
    case ["delete", "2"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.delete_role_v2(rpc_request, request)
    case ["get_members", "2"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.get_role_members_v2(rpc_request, request)
    case ["add_member", "2"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.add_role_member_v2(rpc_request, request)
    case ["remove_member", "2"]:
      if rpc_request is None:
        raise HTTPException(status_code=400, detail='Missing payload')
      return await services.remove_role_member_v2(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC operation')
