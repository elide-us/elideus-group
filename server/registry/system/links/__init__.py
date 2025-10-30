"""Public links registry bindings.

Helpers in this module exchange validated Pydantic models so registries,
providers, and services share consistent payload shapes for public link data.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from .model import HomeLink, NavbarRoute, NavbarRoutesParams

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "HomeLink",
  "NavbarRoute",
  "NavbarRoutesParams",
  "get_home_links_request",
  "get_navbar_routes_request",
  "register",
]


def _request(op: str, params: NavbarRoutesParams | None = None) -> DBRequest:
  payload = params.model_dump(exclude_none=True) if params else {}
  return DBRequest(op=op, payload=payload)


def get_home_links_request() -> DBRequest:
  return _request("db:system:public_links:get_home_links:1")


def get_navbar_routes_request(params: NavbarRoutesParams) -> DBRequest:
  return _request("db:system:public_links:get_navbar_routes:1", params)


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="get_home_links", version=1)
  register_op(name="get_navbar_routes", version=1)
