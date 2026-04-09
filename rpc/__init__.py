"""RPC namespace root.

Exports handlers for each RPC domain with role-based access.
The auth and public domains are exempt from role checks.
"""

from .auth.handler import handle_auth_request
from .public.handler import handle_public_request
from .service.handler import handle_service_request


HANDLERS: dict[str, callable] = {
  "auth": handle_auth_request,
  "public": handle_public_request,
  "service": handle_service_request,
}
