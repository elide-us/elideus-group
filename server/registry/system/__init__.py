"""System domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config, conversations, guilds, links, models, personas, public_users, roles, routes, vars

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "config",
  "conversations",
  "guilds",
  "links",
  "models",
  "public_users",
  "personas",
  "register",
  "roles",
  "routes",
  "vars",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("system")
  config.register(domain.subdomain("config"))
  conversations.register(domain.subdomain("conversations", op_segment="assistant_conversations"))
  guilds.register(domain.subdomain("guilds"))
  links.register(domain.subdomain("links"))
  models.register(domain.subdomain("models", op_segment="assistant_models"))
  personas.register(domain.subdomain("personas", op_segment="assistant_personas"))
  roles.register(domain.subdomain("roles"))
  routes.register(domain.subdomain("routes"))
  public_users.register(domain.subdomain("public_users"))
  vars.register(domain.subdomain("vars"))
