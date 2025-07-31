from .links.handler import handle_links_request
from .user.handler import handle_user_request
from .vars.handler import handle_vars_request

HANDLERS: dict[str, callable] = {
  "user": handle_user_request,
  "links": handle_links_request,
  "vars": handle_vars_request,
}
