from .services import (
  list_roles_v1,
  set_role_v1,
  delete_role_v1,
  get_role_members_v1,
  add_role_member_v1,
  remove_role_member_v1
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): list_roles_v1,
  ("set", "1"): set_role_v1,
  ("delete", "1"): delete_role_v1,
  ("get_members", "1"): get_role_members_v1,
  ("add_member", "1"): add_role_member_v1,
  ("remove_member", "1"): remove_role_member_v1
}
