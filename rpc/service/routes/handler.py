"""Service routes RPC handler.

Dispatches route management operations requiring ROLE_SERVICE_ADMIN.
"""

from fastapi import HTTPException, Request

from server.models import RPCResponse

from . import DISPATCHERS


async def handle_routes_request(parts: list[str], request: Request) -> RPCResponse:
  key = tuple(parts[:2])
  handler = DISPATCHERS.get(key)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC operation')
  return await handler(request)
