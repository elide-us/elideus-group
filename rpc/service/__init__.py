"""Service namespace exposing internal service operations.

Requires ROLE_SERVICE_ADMIN.
"""

from .roles.handler import handle_roles_request
from .routes.handler import handle_routes_request
from .reflection.handler import handle_reflection_request
from .renewals.handler import handle_renewals_request

HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request,
  "routes": handle_routes_request,
  "reflection": handle_reflection_request,
  "renewals": handle_renewals_request,
}
