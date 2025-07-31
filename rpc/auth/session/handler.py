from fastapi import Request, HTTPException
import logging
from rpc.models import RPCResponse
from . import DISPATCHERS

async def handle_session_request(parts: list[str], request: Request) -> RPCResponse:
  logging.debug("handle_session_request parts=%s", parts)
  key = tuple(parts[:2])
  handler = DISPATCHERS.get(key)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC operation")
  return await handler(request)
