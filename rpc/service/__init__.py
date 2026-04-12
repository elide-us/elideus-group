"""Service namespace exposing internal service operations.

Requires ROLE_SERVICE_ADMIN.
"""

from .routes.handler import handle_routes_request
from .objects.handler import handle_objects_request

HANDLERS: dict[str, callable] = {
  "routes": handle_routes_request,
  "objects": handle_objects_request,
}
