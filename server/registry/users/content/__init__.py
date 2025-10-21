"""Content registry bindings for the users domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.users import cache, files, profile, public

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "cache",
  "files",
  "profile",
  "public",
  "register",
]


def register(domain: "DomainRouter") -> None:
  cache.register(domain.subdomain("cache"))
  files.register(domain.subdomain("files"))
  public.register(domain.subdomain("public"))
  profile.register(domain.subdomain("profile"))
