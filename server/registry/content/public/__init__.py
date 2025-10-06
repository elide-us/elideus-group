"""Public content registry bindings for the content domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import links, users

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "links",
  "register",
  "users",
]


def register(domain: "DomainRouter") -> None:
  links.register(domain.subdomain("public.links"))
  users.register(domain.subdomain("public.users"))
