"""Content registry bindings for the users domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import cache, files, public

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "cache",
  "files",
  "public",
  "register",
]


def register(domain: "DomainRouter") -> None:
  cache.register(domain.subdomain("content.cache"))
  files.register(domain.subdomain("content.files"))
  public.register(domain.subdomain("content.public"))
