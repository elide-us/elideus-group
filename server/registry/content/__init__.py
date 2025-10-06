"""Content domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import assistant, profile, public, storage

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "assistant",
  "profile",
  "public",
  "register",
  "storage",
]


def register(router: "RegistryRouter") -> None:
  """Register content domain routes."""

  domain = router.domain("content")
  assistant.register(domain)
  profile.register(domain.subdomain("profile"))
  public.register(domain)
  storage.register(domain)
