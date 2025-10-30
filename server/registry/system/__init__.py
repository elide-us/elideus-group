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
  config.register(router, domain="system", path=("config",))
  conversations.register(router, domain="system", path=("conversations",))
  guilds.register(router, domain="system", path=("guilds",))
  links.register(router, domain="system", path=("links",))
  models.register(router, domain="system", path=("models",))
  personas.register(router, domain="system", path=("personas",))
  roles.register(router, domain="system", path=("roles",))
  routes.register(router, domain="system", path=("routes",))
  public_users.register(router, domain="system", path=("public_users",))
  service_pages.register(router, domain="system", path=("service_pages",))
  public_vars.register(router, domain="system", path=("public_vars",))
