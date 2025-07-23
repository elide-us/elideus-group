from fastapi import Request, HTTPException
from rpc.frontend.vars import services
from rpc.models import RPCResponse

async def handle_vars_request(parts: list[str], request: Request) -> RPCResponse:
  match parts:
    case ["get_version", "1"]:
      return await services.get_version_v1(request)
    case ["get_hostname", "1"]:
      return await services.get_hostname_v1(request)
    case ["get_repo", "1"]:
      return await services.get_repo_v1(request)
    case ["get_ffmpeg_version", "1"]:
      return await services.get_ffmpeg_version_v1(request)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")

