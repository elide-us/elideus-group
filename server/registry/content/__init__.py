"""Content domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import cache, files, public

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "cache",
  "files",
  "public",
  "register",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("content")
  cache.register(domain.subdomain("cache"))
  files.register(domain.subdomain("files"))
  public.register(domain.subdomain("public"))
