"""System route registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "delete_route_request",
  "get_routes_request",
  "register",
  "upsert_route_request",
]

_DEF_PROVIDER = "system.routes"
_PROVIDER_MODULE = "server.registry.system.routes.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "get_routes": "get_routes_v1",
  "upsert_route": "upsert_route_v1",
  "delete_route": "delete_route_v1",
}


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
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
