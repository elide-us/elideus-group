"""Content registry bindings for the users domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import cache, files, profile, public

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
  content_router = domain.subdomain("content")
  cache.register(content_router.subdomain("cache"))
  files.register(content_router.subdomain("files"))
  public.register(content_router.subdomain("public"))
  profile.register(content_router.subdomain("profile"))
