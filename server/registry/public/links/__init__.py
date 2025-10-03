"""Public links registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_home_links_request",
  "get_navbar_routes_request",
  "register",
]

_DEF_PROVIDER = "public.links"
_PROVIDER_MODULE = "server.registry.public.links.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "get_home_links": "get_home_links_v1",
  "get_navbar_routes": "get_navbar_routes_v1",
}


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def get_home_links_request() -> DBRequest:
  return _request("db:public:links:get_home_links:1")


def get_navbar_routes_request(*, role_mask: int) -> DBRequest:
  return _request("db:public:links:get_navbar_routes:1", {"role_mask": role_mask})


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
