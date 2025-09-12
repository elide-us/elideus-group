import logging

from fastapi import HTTPException, Request

from server.models import RPCResponse

from . import DISPATCHERS


async def handle_discord_request(parts: list[str], request: Request) -> RPCResponse:
  """Route Discord auth operations to their handlers."""
  key = tuple(parts[:2])
  handler = DISPATCHERS.get(key)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC operation")
  return await handler(request)
