from .services import (
  account_roles_get_members_v1,
  account_roles_add_member_v1,
  account_roles_remove_member_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  # This module is used by moderators to manage user role membership.
  # This namespace is restricted to those with the ACCOUNT role.
  ("get_members", "1"): account_roles_get_members_v1,
  ("add_member", "1"): account_roles_add_member_v1,
  ("remove_member", "1"): account_roles_remove_member_v1
}

