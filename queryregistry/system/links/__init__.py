"""System links query handler package."""

from queryregistry.models import DBRequest


def get_home_links_request() -> DBRequest:
  return DBRequest(op="db:system:links:get_home_links:1", payload={})


def get_navbar_routes_request(role_mask: int | None = None) -> DBRequest:
  payload: dict[str, object] = {}
  if role_mask is not None:
    payload["role_mask"] = role_mask
  return DBRequest(op="db:system:links:get_navbar_routes:1", payload=payload)


__all__ = [
  "get_home_links_request",
  "get_navbar_routes_request",
]
