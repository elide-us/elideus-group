from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.storage.files.handler import handle_files_request

async def handle_storage_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ['files', *rest]:
      return await handle_files_request(rest, rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
