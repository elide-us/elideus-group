from .services import (
  system_roles_get_roles_v1,
  system_roles_upsert_role_v1,
  system_roles_delete_role_v1,
  system_roles_get_role_members_v1,
  system_roles_add_role_member_v1,
  system_roles_remove_member_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  """
    These functions are used to make changes to user role assignments.
    The roles are stored in the database. Each role has a bitmask flag.
    Users have a combined bitmask value stored for all roles assigned.
    This namespace is restricted to users with the SYSTEM role.
  """
  ("get_roles", "1"): system_roles_get_roles_v1,
  ("upsert_role", "1"): system_roles_upsert_role_v1,
  ("delete_role", "1"): system_roles_delete_role_v1,
  ("get_role_members", "1"): system_roles_get_role_members_v1,
  ("add_role_member", "1"): system_roles_add_role_member_v1,
  ("remove_role_member", "1"): system_roles_remove_member_v1
}

