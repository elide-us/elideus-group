"""System domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import (
  config,
  conversations,
  guilds,
  links,
  models,
  personas,
  public_users,
  public_vars,
  roles,
  routes,
  service_pages,
)

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "config",
  "conversations",
  "guilds",
  "links",
  "models",
  "personas",
  "public_users",
  "public_vars",
  "register",
  "roles",
  "routes",
  "service_pages",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("system")
  config.register(domain.subdomain("config"))
  conversations.register(domain.subdomain("conversations"))
  guilds.register(domain.subdomain("guilds"))
  links.register(domain.subdomain("links"))
  models.register(domain.subdomain("models"))
  personas.register(domain.subdomain("personas"))
  roles.register(domain.subdomain("roles"))
  routes.register(domain.subdomain("routes"))
  public_users.register(domain.subdomain("public_users"))
  service_pages.register(domain.subdomain("service_pages"))
  public_vars.register(domain.subdomain("public_vars"))
