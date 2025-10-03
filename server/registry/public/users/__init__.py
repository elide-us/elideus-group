"""Public users registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_profile_request",
  "get_published_files_request",
  "register",
]

_DEF_PROVIDER = "public.users"
_PROVIDER_MODULE = "server.registry.public.users.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "get_profile": "get_profile_v1",
  "get_published_files": "get_published_files_v1",
}


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def get_profile_request(*, guid: str) -> DBRequest:
  return _request("db:public:users:get_profile:1", {"guid": guid})


def get_published_files_request(*, guid: str) -> DBRequest:
  return _request("db:public:users:get_published_files:1", {"guid": guid})


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
