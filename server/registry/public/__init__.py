"""Public domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import links, users, vars as _vars

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "links",
  "users",
  "vars",
  "register",
]

# expose module under original name while avoiding shadowing built-in ``vars``
vars = _vars


def register(router: "RegistryRouter") -> None:
  domain = router.domain("public")
  links.register(domain.subdomain("links"))
  users.register(domain.subdomain("users"))
  vars.register(domain.subdomain("vars"))
