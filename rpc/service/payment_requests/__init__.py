"""Service payment requests RPC namespace.

Requires ROLE_SERVICE_ADMIN.
"""

from .services import service_payment_requests_create_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("create", "1"): service_payment_requests_create_v1,
}
