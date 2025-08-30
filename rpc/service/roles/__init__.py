from .services import (
  service_roles_get_roles_v1,
  service_roles_upsert_role_v1,
  service_roles_delete_role_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  # Functions for managing role definitions. Roles are stored in the database
  # with bitmask flags. This namespace is restricted to users with the
  # ACCOUNT_ADMIN role.
  ("get_roles", "1"): service_roles_get_roles_v1,
  ("upsert_role", "1"): service_roles_upsert_role_v1,
  ("delete_role", "1"): service_roles_delete_role_v1,
}

