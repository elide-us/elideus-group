from .services import (
  admin_roles_get_members_v1,
  admin_roles_add_member_v1,
  admin_roles_remove_member_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  # This module is used by moderators to manage user role membership.
  # This namespace is restricted to those with the ADMIN role.
  ("get_members", "1"): admin_roles_get_members_v1,
  ("add_member", "1"): admin_roles_add_member_v1,
  ("remove_member", "1"): admin_roles_remove_member_v1
}

