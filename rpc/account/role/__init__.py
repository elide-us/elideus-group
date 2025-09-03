from .services import (
  account_role_get_roles_v1,
  account_role_get_role_members_v1,
  account_role_add_role_member_v1,
  account_role_remove_role_member_v1,
  account_role_upsert_role_v1,
  account_role_delete_role_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_roles", "1"): account_role_get_roles_v1,
  ("get_role_members", "1"): account_role_get_role_members_v1,
  ("add_role_member", "1"): account_role_add_role_member_v1,
  ("remove_role_member", "1"): account_role_remove_role_member_v1,
  ("upsert_role", "1"): account_role_upsert_role_v1,
  ("delete_role", "1"): account_role_delete_role_v1,
}
