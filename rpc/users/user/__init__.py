from .services import (
  users_user_get_profile_v1,
  users_user_set_display_v1,
  users_user_set_optin_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_profile", "1"): users_user_get_profile_v1,
  ("set_display", "1"): users_user_set_display_v1,
  ("set_optin", "1"): users_user_set_optin_v1
}

