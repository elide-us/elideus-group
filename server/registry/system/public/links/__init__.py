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


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def get_home_links_request() -> DBRequest:
  return _request("db:system:public_links:get_home_links:1")


def get_navbar_routes_request(*, role_mask: int) -> DBRequest:
  return _request("db:system:public_links:get_navbar_routes:1", {"role_mask": role_mask})


def register(router: "SubdomainRouter") -> None:
  router.add_function("get_home_links", version=1)
  router.add_function("get_navbar_routes", version=1)
