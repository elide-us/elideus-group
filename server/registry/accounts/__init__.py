"""Accounts domain registry bindings."""

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
  """Register accounts domain routes."""
  domain = router.domain("accounts")
  profile.register(domain.subdomain("profile"))
