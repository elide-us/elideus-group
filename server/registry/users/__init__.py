"""Users domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import profile

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "profile",
  "register",
]


def register(router: "RegistryRouter") -> None:
  """Register users domain routes."""

  domain = router.domain("users")
  profile.register(domain.subdomain("profile"))
