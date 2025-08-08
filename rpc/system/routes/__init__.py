"""System routes RPC namespace.

Requires ROLE_SYSTEM_ADMIN.
"""

from .services import (
  system_routes_delete_route_v1,
  system_routes_get_routes_v1,
  system_routes_upsert_route_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_routes", "1"): system_routes_get_routes_v1,
  ("upsert_route", "1"): system_routes_upsert_route_v1,
  ("delete_route", "1"): system_routes_delete_route_v1
}

