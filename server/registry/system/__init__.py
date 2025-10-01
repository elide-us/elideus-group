"""System domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config, roles, routes

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "config",
  "register",
  "roles",
  "routes",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("system")
  config.register(domain.subdomain("config"))
  roles.register(domain.subdomain("roles"))
  routes.register(domain.subdomain("routes"))
