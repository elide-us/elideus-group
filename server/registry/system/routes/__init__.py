"""System route registry bindings."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "delete_route_request",
  "get_routes_request",
  "register",
  "upsert_route_request",
]


def get_routes_request() -> DBRequest:
  return DBRequest(op="db:system:routes:get_routes:1", payload={})


def upsert_route_request(
  *,
  path: str,
  name: str,
  icon: str | None,
  sequence: int,
  roles: int,
) -> DBRequest:
  return DBRequest(op="db:system:routes:upsert_route:1", payload={
    "path": path,
    "name": name,
    "icon": icon,
    "sequence": sequence,
    "roles": roles,
  })


def delete_route_request(path: str) -> DBRequest:
  return DBRequest(op="db:system:routes:delete_route:1", payload={"path": path})


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="get_routes", version=1)
  register_op(name="upsert_route", version=1)
  register_op(name="delete_route", version=1)
