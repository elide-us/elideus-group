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
  content_router = domain.subdomain("content", op_segment="")
  cache.register(content_router.subdomain("cache", op_segment="content_cache"))
  files.register(content_router.subdomain("files", op_segment="content_files"))
  public.register(content_router.subdomain("public", op_segment="content_public"))
  profile.register(content_router.subdomain("profile", op_segment="content_profile"))
