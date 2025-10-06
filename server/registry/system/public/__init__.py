"""Public registry bindings for the system domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import links as _links, vars as _vars

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "links",
  "register",
  "vars",
]

links = _links
vars = _vars


def register(domain: "DomainRouter") -> None:
  links.register(domain.subdomain("public.links"))
  vars.register(domain.subdomain("public.vars"))
