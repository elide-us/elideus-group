"""Users domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import security

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "register",
  "security",
]


def register(router: "RegistryRouter") -> None:
  """Register users domain routes."""

  domain = router.domain("users")
  security.register(domain)
