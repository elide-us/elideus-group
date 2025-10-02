"""Account domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import users

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "users",
  "register",
]


def register(router: "RegistryRouter") -> None:
  """Register account domain routes."""
  domain = router.domain("account")
  users.register(domain.subdomain("users"))
