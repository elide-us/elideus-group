"""Security RPC namespace.

Handles security operations requiring ROLE_SECURITY_ADMIN.
Auth and public domains are exempt from role checks.
"""

from fastapi import HTTPException, Request

from rpc.models import RPCResponse

from . import HANDLERS


async def handle_security_request(parts: list[str], request: Request) -> RPCResponse:
  subdomain = parts[0]
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC subdomain')
  return await handler(parts[1:], request)

