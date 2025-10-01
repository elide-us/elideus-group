"""Content cache registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "register",
]


_DEF_PROVIDER = "content.cache"


def _alias(key: str) -> str:
  return f"db:storage:cache:{key}:1"


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "list",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.list",
    aliases=[_alias("list")],
  )
  router.add_function(
    "replace_user",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.replace_user",
    aliases=[_alias("replace_user")],
  )
  router.add_function(
    "upsert",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.upsert",
    aliases=[_alias("upsert")],
  )
  router.add_function(
    "delete",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.delete",
    aliases=[_alias("delete")],
  )
  router.add_function(
    "delete_folder",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.delete_folder",
    aliases=[_alias("delete_folder")],
  )
  router.add_function(
    "set_public",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.set_public",
    aliases=[_alias("set_public")],
  )
  router.add_function(
    "set_reported",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.set_reported",
    aliases=[_alias("set_reported")],
  )
  router.add_function(
    "count_rows",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.count_rows",
    aliases=[_alias("count_rows")],
  )
