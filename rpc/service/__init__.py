"""Service namespace exposing internal service operations.

Requires ROLE_SERVICE_ADMIN.
"""

from .routes.handler import handle_routes_request
from .reflection.handler import handle_reflection_request
from .rpcdispatch.handler import handle_rpcdispatch_request

HANDLERS: dict[str, callable] = {
  "routes": handle_routes_request,
  "reflection": handle_reflection_request,
  "rpcdispatch": handle_rpcdispatch_request,
}
