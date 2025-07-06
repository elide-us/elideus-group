"""Server package exposing router modules for external import.

This allows tests and application code to import the configured routers using
`from server import rpc_router` instead of reaching into the routers package directly."""

from . import lifespan
from .routers import rpc_router, web_router

__all__ = ["rpc_router", "web_router", "lifespan"]
