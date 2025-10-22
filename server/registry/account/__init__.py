"""Account domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import actions, accounts, content, enablements, oauth, providers, session

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "actions",
  "accounts",
  "content",
  "enablements",
  "providers",
  "register",
  "session",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("account")
  content.register(domain)
  accounts.register(domain.subdomain("accounts"))
  actions.register(domain.subdomain("actions"))
  enablements.register(domain.subdomain("enablements"))
  providers.register(domain.subdomain("providers"))
  oauth.register(domain.subdomain("oauth"))
  session.register(domain.subdomain("session"))
