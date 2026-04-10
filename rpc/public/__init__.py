from .links.handler import handle_links_request
from .route.handler import handle_route_request
from .vars.handler import handle_vars_request


HANDLERS: dict[str, callable] = {
  "links": handle_links_request,
  "route": handle_route_request,
  "vars": handle_vars_request,
}
