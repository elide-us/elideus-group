"""System route registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from . import mssql  # noqa: F401

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "delete_route_request",
  "get_routes_request",
  "register",
  "upsert_route_request",
]

_DEF_PROVIDER = "system.routes"


def get_routes_request() -> DBRequest:
  return DBRequest(op="db:system:routes:get_routes:1", params={})


def upsert_route_request(
  *,
  path: str,
  name: str,
  icon: str | None,
  sequence: int,
  roles: int,
) -> DBRequest:
  return DBRequest(op="db:system:routes:upsert_route:1", params={
    "path": path,
    "name": name,
    "icon": icon,
    "sequence": sequence,
    "roles": roles,
  })


def delete_route_request(path: str) -> DBRequest:
  return DBRequest(op="db:system:routes:delete_route:1", params={"path": path})


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "get_routes",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.get_routes",
  )
  router.add_function(
    "upsert_route",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.upsert_route",
  )
  router.add_function(
    "delete_route",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.delete_route",
  )
