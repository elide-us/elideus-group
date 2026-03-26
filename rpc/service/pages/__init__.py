"""Service pages RPC namespace.

Requires ROLE_SERVICE_ADMIN.
"""

from .services import (
  service_pages_create_v1,
  service_pages_delete_v1,
  service_pages_list_v1,
  service_pages_update_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): service_pages_list_v1,
  ("create", "1"): service_pages_create_v1,
  ("update", "1"): service_pages_update_v1,
  ("delete", "1"): service_pages_delete_v1,
}
