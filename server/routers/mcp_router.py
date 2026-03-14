"""MCP protocol router for delegating /mcp requests to the SDK session manager."""

from fastapi import APIRouter
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from server.mcp_server import mcp_asgi_handler

router = APIRouter()


class _MCPRouteHandler:
  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    await mcp_asgi_handler(scope, receive, send)


router.routes.append(
  Route("/mcp", endpoint=_MCPRouteHandler(), methods=["GET", "POST", "DELETE"])
)
