"""System routes query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import RoutePathParams, UpsertRouteParams

__all__ = [
  "delete_route_request",
  "get_routes_request",
  "upsert_route_request",
]


def get_routes_request() -> DBRequest:
  return DBRequest(op="db:system:routes:get_routes:1", payload={})


def upsert_route_request(params: UpsertRouteParams) -> DBRequest:
  return DBRequest(op="db:system:routes:upsert_route:1", payload=params.model_dump())


def delete_route_request(params: RoutePathParams) -> DBRequest:
  return DBRequest(op="db:system:routes:delete_route:1", payload=params.model_dump())
