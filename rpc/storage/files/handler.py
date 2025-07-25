from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.storage.files import services

async def handle_files_request(parts: list[str], rpc_request: RPCRequest, request: Request) -> RPCResponse:
  match parts:
    case ["list", "1"]:
      return await services.list_files_v1(rpc_request, request)
    case ["delete", "1"]:
      return await services.delete_file_v1(rpc_request, request)
    case ["upload", "1"]:
      return await services.upload_file_v1(rpc_request, request)
    case _:
      raise HTTPException(status_code=404, detail='Unknown RPC operation')
