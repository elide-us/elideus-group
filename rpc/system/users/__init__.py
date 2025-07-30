from services import (
  get_users_v1,
  get_user_roles_v1,
  set_user_roles_v1,
  list_available_roles_v1,
  get_user_profile_v1,
  set_user_credits_v1,
  enable_user_storage_v1
) 

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): get_users_v1,
  ("get_roles", "1"): get_user_roles_v1,
  ("set_roles", "1"): set_user_roles_v1,
  ("list_roles", "1"): list_available_roles_v1,
  ("get_profile", "1"): get_user_profile_v1,
  ("set_credits", "1"): set_user_credits_v1,
  ("enable_storage", "1"): enable_user_storage_v1
}