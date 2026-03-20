"""Service renewals RPC namespace.

Requires ROLE_SERVICE_ADMIN.
"""

from .services import (
  service_renewals_delete_v1,
  service_renewals_get_v1,
  service_renewals_list_v1,
  service_renewals_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("delete", "1"): service_renewals_delete_v1,
  ("get", "1"): service_renewals_get_v1,
  ("list", "1"): service_renewals_list_v1,
  ("upsert", "1"): service_renewals_upsert_v1,
}
