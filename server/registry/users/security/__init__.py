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
  accounts.register(domain.subdomain("security.accounts"))
  identities.register(domain.subdomain("security.identities"))
  oauth.register(domain.subdomain("security.oauth"))
  sessions.register(domain.subdomain("security.sessions"))
