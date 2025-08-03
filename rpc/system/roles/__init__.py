from .services import (system_roles_get_members_v1,
                       system_roles_add_member_v1,
                       system_roles_remove_member_v1)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_members", "1"): system_roles_get_members_v1,
  ("add_member", "1"): system_roles_add_member_v1,
  ("remove_member", "1"): system_roles_remove_member_v1
}

