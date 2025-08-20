"""System namespace for managing routes and configuration.

Requires ROLE_SYSTEM_ADMIN.
"""

from .config.handler import handle_config_request
from .routes.handler import handle_routes_request
from .roles.handler import handle_roles_request

HANDLERS: dict[str, callable] = {
  "routes": handle_routes_request,
  "config": handle_config_request,
  "roles": handle_roles_request
}

