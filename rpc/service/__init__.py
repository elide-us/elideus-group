"""Service namespace exposing internal service operations.

Requires ROLE_SERVICE_ADMIN.
"""

from .roles.handler import handle_roles_request
from .services import service_health_check_v1

HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request,
}

DISPATCHERS: dict[tuple[str, str], callable] = {
  # Requires ROLE_SERVICE_ADMIN.
  ("health_check", "1"): service_health_check_v1,
}
