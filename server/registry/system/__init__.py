"""System domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import assistant, config, public, roles, routes

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "config",
  "public",
  "register",
  "roles",
  "routes",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("system")
  assistant.register(domain)
  config.register(domain.subdomain("config"))
  public.register(domain)
  roles.register(domain.subdomain("roles"))
  routes.register(domain.subdomain("routes"))
