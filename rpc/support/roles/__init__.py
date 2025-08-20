from .services import (
  support_roles_get_members_v1,
  support_roles_add_member_v1,
  support_roles_remove_member_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  # This module is used by moderators to manage user role membership.
  # This namespace is restricted to those with the SUPPORT role.
  ("get_members", "1"): support_roles_get_members_v1,
  ("add_member", "1"): support_roles_add_member_v1,
  ("remove_member", "1"): support_roles_remove_member_v1
}

