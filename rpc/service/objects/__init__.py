"""Service objects RPC namespace.

Requires ROLE_SERVICE_ADMIN.
"""

from .services import (
  service_objects_read_object_tree_children_v1,
  service_objects_read_object_tree_detail_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("read_object_tree_children", "1"): service_objects_read_object_tree_children_v1,
  ("read_object_tree_detail", "1"): service_objects_read_object_tree_detail_v1,
}
