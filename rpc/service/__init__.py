"""Service namespace exposing internal service operations.

Requires ROLE_SERVICE_ADMIN.
"""

from .roles.handler import handle_roles_request

HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request,
}
