"""Content public registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "register",
]


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "list_public",
    version=1,
    provider_map="content.public.list_public",
  )
  router.add_function(
    "list_reported",
    version=1,
    provider_map="content.public.list_reported",
  )
  router.add_function(
    "get_public_files",
    version=1,
    provider_map="content.public.get_public_files",
    aliases=["db:public:gallery:get_public_files:1"],
  )
