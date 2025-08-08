"""Administrative namespace for user and role management.

Requires ROLE_ADMIN_SUPPORT.
"""

from .roles.handler import handle_roles_request
from .users.handler import handle_users_request

HANDLERS: dict[str, callable] = {
  "users": handle_users_request,
  "roles": handle_roles_request,
}
