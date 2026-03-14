import logging
import os
from typing import TYPE_CHECKING, Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount

if TYPE_CHECKING:
  from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

_MCP_TOKEN = os.getenv("MCP_AGENT_TOKEN")

mcp: Any | None = None
if _MCP_TOKEN:
  from mcp.server.fastmcp import FastMCP

  mcp = FastMCP("elideus-group")


class MCPAuthMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next) -> Response:
    if not _MCP_TOKEN:
      return JSONResponse(status_code=503, content={"detail": "MCP token not configured"})

    if request.headers.get("authorization") != f"Bearer {_MCP_TOKEN}":
      return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


# Module-level session manager (initialized when token is configured)
session_manager: StreamableHTTPSessionManager | None = None


def _build_mcp_app() -> None:
  """Initialize the module-level session_manager."""
  global session_manager
  from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

  session_manager = StreamableHTTPSessionManager(
    app=mcp._mcp_server,
    json_response=True,
    stateless=True,
  )


def get_mcp_app() -> Starlette | None:
  """Return the MCP ASGI app wrapped with auth middleware, or None if unconfigured."""
  if not _MCP_TOKEN:
    logging.info("[MCP] skipped (MCP_AGENT_TOKEN not set)")
    return None

  _build_mcp_app()

  mcp_inner = Starlette(
    routes=[
      Mount("/mcp", app=session_manager.handle_request),
    ],
  )

  app = Starlette(middleware=[Middleware(MCPAuthMiddleware)])
  app.mount("/", mcp_inner)
  return app
