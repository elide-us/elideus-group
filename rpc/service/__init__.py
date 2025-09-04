"""Service namespace exposing internal service operations.

Requires ROLE_SERVICE_ADMIN.
"""

from .roles.handler import handle_roles_request
from .routes.handler import handle_routes_request

HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request,
  "routes": handle_routes_request,
}
