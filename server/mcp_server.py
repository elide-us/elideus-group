"""MCP server bridge mounted into the FastAPI application."""

from __future__ import annotations

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send


def _auth_challenge_headers(hostname: str) -> dict[str, str]:
  return {
    'WWW-Authenticate': f'Bearer resource_metadata="https://{hostname}/.well-known/oauth-protected-resource"'
  }


async def mcp_asgi_handler(scope: Scope, receive: Receive, send: Send) -> None:
  request = Request(scope, receive)
  module = request.app.state.mcp_io_service
  await module.on_ready()

  if module.session_manager is None:
    response = JSONResponse({'error': 'MCP not configured'}, status_code=503)
    await response(scope, receive, send)
    return

  auth = request.headers.get('authorization', '')
  if not auth.startswith('Bearer '):
    response = JSONResponse(
      {'error': 'Unauthorized'},
      status_code=401,
      headers=_auth_challenge_headers(module.hostname or 'localhost'),
    )
    await response(scope, receive, send)
    return

  token = auth[7:]
  identity = await module.resolve_identity(token)
  if identity is None:
    response = JSONResponse(
      {'error': 'Unauthorized'},
      status_code=401,
      headers=_auth_challenge_headers(module.hostname or 'localhost'),
    )
    await response(scope, receive, send)
    return

  token_handle = module._AUTH_CONTEXT.set({'token': token, 'identity': identity})
  try:
    await module.session_manager.handle_request(scope, receive, send)
  except HTTPException:
    raise
  finally:
    module._AUTH_CONTEXT.reset(token_handle)
