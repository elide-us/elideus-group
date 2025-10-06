"""Users domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import credits, profile

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "credits",
  "profile",
  "register",
]


def register(router: "RegistryRouter") -> None:
  """Register users domain routes."""

  domain = router.domain("users")
  credits.register(domain.subdomain("credits"))
  profile.register(domain.subdomain("profile"))
