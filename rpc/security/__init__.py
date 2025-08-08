"""Security namespace for role and permission management.

Requires ROLE_SECURITY_ADMIN.
"""

from .roles.handler import handle_roles_request


HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request
}

