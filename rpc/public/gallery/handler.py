from fastapi import HTTPException, Request
from server.models import RPCResponse
from . import DISPATCHERS

async def handle_gallery_request(parts: list[str], request: Request) -> RPCResponse:
  key = tuple(parts[:2])
  handler = DISPATCHERS.get(key)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC operation")
  return await handler(request)
