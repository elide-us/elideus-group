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
  content.register(router, domain="account")
  accounts.register(router, domain="account", path=("accounts",))
  actions.register(router, domain="account", path=("actions",))
  enablements.register(router, domain="account", path=("enablements",))
  providers.register(router, domain="account", path=("providers",))
  oauth.register(router, domain="account", path=("oauth",))
  session.register(router, domain="account", path=("session",))
