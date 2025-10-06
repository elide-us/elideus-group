"""Public registry bindings for the users domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import users

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "register",
  "users",
]


def register(domain: "DomainRouter") -> None:
  users.register(domain.subdomain("public.users"))
