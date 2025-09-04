"""System namespace for managing configuration and roles.

Requires ROLE_SYSTEM_ADMIN.
"""

from .config.handler import handle_config_request
from .roles.handler import handle_roles_request

HANDLERS: dict[str, callable] = {
  "config": handle_config_request,
  "roles": handle_roles_request,
}

