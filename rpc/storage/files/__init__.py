from fastapi import Request
from rpc.helpers import get_rpcrequest_from_request
from . import services


def _wrap(func):
  async def wrapped(request: Request):
    rpc_request, _ = await get_rpcrequest_from_request(request)
    return await func(rpc_request, request)
  return wrapped

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): _wrap(services.list_files_v1),
  ("delete", "1"): _wrap(services.delete_file_v1),
  ("upload", "1"): _wrap(services.upload_file_v1),
}
