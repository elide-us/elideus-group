"""Public links registry helpers.

Helpers in this module exchange validated Pydantic models so registries,
providers, and services share consistent payload shapes for public link data.
"""

from __future__ import annotations

from server.registry.types import DBRequest

from .model import HomeLink, NavbarRoute, NavbarRoutesParams

__all__ = [
  "HomeLink",
  "NavbarRoute",
  "NavbarRoutesParams",
  "get_home_links_request",
  "get_navbar_routes_request",
]


def _request(op: str, params: NavbarRoutesParams | None = None) -> DBRequest:
  payload = params.model_dump(exclude_none=True) if params else {}
  return DBRequest(op=op, payload=payload)


def get_home_links_request() -> DBRequest:
  return _request("db:system:links:get_home_links:1")


def get_navbar_routes_request(params: NavbarRoutesParams) -> DBRequest:
  return _request("db:system:links:get_navbar_routes:1", params)
