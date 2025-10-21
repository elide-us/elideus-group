"""Users domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import accounts, content, providers

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "accounts",
  "content",
  "providers",
  "register",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("users")
  content.register(domain)
  accounts.register(domain.subdomain("accounts", op_segment="account"))
  providers.register(domain.subdomain("providers"))
