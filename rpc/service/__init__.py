"""Service namespace exposing internal service operations.

Requires ROLE_SERVICE_ADMIN.
"""

from .roles.handler import handle_roles_request
from .routes.handler import handle_routes_request
from .reflection.handler import handle_reflection_request
from .renewals.handler import handle_renewals_request
from .payment_requests.handler import handle_payment_requests_request
from .rpcdispatch.handler import handle_rpcdispatch_request

HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request,
  "routes": handle_routes_request,
  "reflection": handle_reflection_request,
  "renewals": handle_renewals_request,
  "payment_requests": handle_payment_requests_request,
  "rpcdispatch": handle_rpcdispatch_request,
}
