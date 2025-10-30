"""Content registry bindings for the account domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.account import cache, files, profile, public

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "cache",
  "files",
  "profile",
  "public",
  "register",
]


def register(router: "RegistryRouter", *, domain: str) -> None:
  cache.register(router, domain=domain, path=("cache",))
  files.register(router, domain=domain, path=("files",))
  public.register(router, domain=domain, path=("public",))
  profile.register(router, domain=domain, path=("profile",))
