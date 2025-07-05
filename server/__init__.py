"""Server package exposing router modules for external import.

This allows tests and application code to import the configured routers using
`from server import rpc_router` instead of reaching into the routers package
directly."""

from .routers import rpc as rpc_router
from .routers import web as web_router

__all__ = ["rpc_router", "web_router"]
