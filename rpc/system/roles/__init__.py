"""System roles RPC namespace.

Requires ROLE_SYSTEM_ADMIN.
"""

from .services import (
  system_roles_get_roles_v1,
  system_roles_upsert_role_v1,
  system_roles_delete_role_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_roles", "1"): system_roles_get_roles_v1,
  ("upsert_role", "1"): system_roles_upsert_role_v1,
  ("delete_role", "1"): system_roles_delete_role_v1,
}
