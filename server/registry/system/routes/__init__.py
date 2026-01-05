"""System route registry bindings."""

from __future__ import annotations

from server.registry.types import DBRequest



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
