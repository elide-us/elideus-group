"""Content files registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "register",
]


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "set_gallery",
    version=1,
    provider_map="content.files.set_gallery",
    aliases=["db:storage:files:set_gallery:1"],
  )
