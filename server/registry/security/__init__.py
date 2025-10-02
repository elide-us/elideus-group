"""Security domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import accounts, identities, oauth, sessions

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "accounts",
  "identities",
  "oauth",
  "register",
  "sessions",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("security")
  accounts.register(domain.subdomain("accounts"))
  identities.register(domain.subdomain("identities"))
  oauth.register(domain.subdomain("oauth"))
  sessions.register(domain.subdomain("sessions"))
