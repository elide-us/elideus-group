# MIGRATION NOTE: DROP TABLE frontend_links (data migrated to system_objects_page_data_bindings)
from .route.handler import handle_route_request
from .vars.handler import handle_vars_request
from .auth.handler import handle_auth_request


HANDLERS: dict[str, callable] = {
  "route": handle_route_request,
  "vars": handle_vars_request,
  "auth": handle_auth_request,
}
