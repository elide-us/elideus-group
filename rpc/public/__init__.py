from .links.handler import handle_links_request
from .vars.handler import handle_vars_request
from .users.handler import handle_users_request


HANDLERS: dict[str, callable] = {
  "links": handle_links_request,
  "vars": handle_vars_request,
  "users": handle_users_request,
}

