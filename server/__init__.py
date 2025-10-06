"""Server package exports with lazy router imports to avoid circular deps."""

from . import lifespan
from .helpers.logging import configure_root_logging


__all__ = [
  "rpc_router",
  "web_router",
  "lifespan",
  "configure_root_logging",
]


def __getattr__(name):
  if name == "rpc_router":
    from .routers import rpc_router as _rpc_router
    return _rpc_router
  if name == "web_router":
    from .routers import web_router as _web_router
    return _web_router
  raise AttributeError(f"module 'server' has no attribute {name!r}")
