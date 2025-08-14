from typing import Any, Optional

from pydantic import BaseModel, Field

from . import lifespan
from .routers import rpc_router, web_router
from .helpers.logging import configure_root_logging


class AuthContext(BaseModel):
  user_guid: Optional[str] = None
  role_mask: int = 0
  roles: list[str] = Field(default_factory=list)
  provider: Optional[str] = None
  claims: dict[str, Any] = Field(default_factory=dict)

__all__ = [
  "rpc_router",
  "web_router",
  "lifespan",
  "configure_root_logging",
  "AuthContext",
]
