"""System public query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import RoutePathParams, UpsertRouteParams

__all__ = [
  "delete_route_request",
  "get_cms_tree_for_path_request",
  "get_config_value_request",
  "get_home_links_request",
  "get_navbar_routes_request",
  "get_routes_request",
  "list_frontend_pages_request",
  "upsert_route_request",
]


def get_home_links_request() -> DBRequest:
  return DBRequest(op="db:system:public:get_home_links:1", payload={})


def get_navbar_routes_request(role_mask: int | None = None) -> DBRequest:
  payload: dict[str, object] = {}
  if role_mask is not None:
    payload["role_mask"] = role_mask
  return DBRequest(op="db:system:public:get_navbar_routes:1", payload=payload)


def get_routes_request() -> DBRequest:
  return DBRequest(op="db:system:public:get_routes:1", payload={})


def list_frontend_pages_request() -> DBRequest:
  return DBRequest(op="db:system:public:list_frontend_pages:1", payload={})


def upsert_route_request(params: UpsertRouteParams) -> DBRequest:
  return DBRequest(op="db:system:public:upsert_route:1", payload=params.model_dump())


def delete_route_request(params: RoutePathParams) -> DBRequest:
  return DBRequest(op="db:system:public:delete_route:1", payload=params.model_dump())


def get_cms_tree_for_path_request(path: str) -> DBRequest:
  return DBRequest(op="db:system:public:get_cms_tree_for_path:1", payload={"path": path})


def get_config_value_request(key: str) -> DBRequest:
  return DBRequest(op="db:system:public:get_config_value:1", payload={"key": key})
