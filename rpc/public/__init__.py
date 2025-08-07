from .links.handler import handle_links_request
from .vars.handler import handle_vars_request


HANDLERS: dict[str, callable] = {
  "links": handle_links_request,
  "vars": handle_vars_request,
}

