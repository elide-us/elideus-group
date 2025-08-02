from .services import (add_role_member_v1, delete_role_v1, get_role_members_v1,
                       get_roles_v1, remove_role_member_v1, set_role_v1)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_roles", "1"): get_roles_v1,
  ("set_role", "1"): set_role_v1,
  ("delete_role", "1"): delete_role_v1,
  ("get_members", "1"): get_role_members_v1,
  ("add_member", "1"): add_role_member_v1,
  ("remove_member", "1"): remove_role_member_v1
}
