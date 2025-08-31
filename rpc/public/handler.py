"""Handlers for the public namespace accessed by the frontend.

These operations serve unauthenticated data and are exempt from
security role checks.
"""

from fastapi import HTTPException, Request

from server.models import RPCResponse

from . import HANDLERS

REQUIRED_ROLE_MASK = 0


async def handle_public_request(parts: list[str], request: Request) -> RPCResponse:
  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)
