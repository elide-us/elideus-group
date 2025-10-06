"""Users domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import content, public, security

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "content",
  "public",
  "register",
  "security",
]


def register(router: "RegistryRouter") -> None:
  """Register users domain routes."""

  domain = router.domain("users")
  content.register(domain)
  public.register(domain.subdomain("public"))
  security.register(domain)
