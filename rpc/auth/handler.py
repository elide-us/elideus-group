"""Handlers for the authentication namespace.

These operations manage login and session flow and are exempt from
security role checks.
"""

from fastapi import HTTPException, Request

from server.models import RPCResponse

from . import HANDLERS


async def handle_auth_request(parts: list[str], request: Request) -> RPCResponse:
  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown RPC subdomain")
  return await handler(parts[1:], request)
