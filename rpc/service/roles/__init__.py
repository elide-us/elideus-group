from .services import (
  service_roles_get_roles_v1,
  service_roles_upsert_role_v1,
  service_roles_delete_role_v1,
  service_roles_get_role_members_v1,
  service_roles_add_role_member_v1,
  service_roles_remove_role_member_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  # These functions are for making changes to the role definitions and
  # managing role membership. The roles are stored in the database.
  # Each role has a bitmask flag. Users have a combined bitmask value
  # stored for all roles assigned.
  # This namespace is restricted to users with the SERVICE role.
  ("get_roles", "1"): service_roles_get_roles_v1,
  ("upsert_role", "1"): service_roles_upsert_role_v1,
  ("delete_role", "1"): service_roles_delete_role_v1,
  ("get_role_members", "1"): service_roles_get_role_members_v1,
  ("add_role_member", "1"): service_roles_add_role_member_v1,
  ("remove_role_member", "1"): service_roles_remove_role_member_v1,
}

