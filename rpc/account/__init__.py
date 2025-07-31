from .users.handler import handle_users_request
from .roles.handler import handle_roles_request

HANDLERS: dict[str, callable] = {
  "users": handle_users_request,
  "roles": handle_roles_request,
}
