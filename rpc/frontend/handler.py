from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.frontend.user.handler import handle_user_request
from rpc.frontend.links.handler import handle_links_request
from rpc.frontend.vars.handler import handle_vars_request
from rpc.frontend.files.handler import handle_files_request

async def handle_frontend_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ['user', *rest]:
      return await handle_user_request(rest, rpc_request, request)
    case ['links', *rest]:
      return await handle_links_request(rest, request)
    case ['vars', *rest]:
      return await handle_vars_request(rest, request)
    case ['files', *rest]:
      return await handle_files_request(rest, rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
