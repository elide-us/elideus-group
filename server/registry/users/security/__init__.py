"""Security registry bindings for the users domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import accounts, identities, oauth, sessions

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "accounts",
  "identities",
  "oauth",
  "register",
  "sessions",
]


def register(domain: "DomainRouter") -> None:
  security_router = domain.subdomain("security")
  accounts.register(security_router.subdomain("accounts"))
  identities.register(security_router.subdomain("identities"))
  oauth.register(security_router.subdomain("oauth"))
  sessions.register(security_router.subdomain("sessions"))
