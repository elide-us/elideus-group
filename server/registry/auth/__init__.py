"""Authentication domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import oauth, providers, session

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "oauth",
  "providers",
  "session",
  "register",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("auth")
  providers.register(domain.subdomain("providers"))
  oauth.register(domain)
  session.register(domain.subdomain("session"))
