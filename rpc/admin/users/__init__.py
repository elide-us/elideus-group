from .services import (
  admin_users_get_profile_v1,
  admin_users_reset_display_v1,
  admin_users_set_credits_v1,
  admin_users_enable_storage_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  # This module is used by moderators to manage user accounts.
  # This namespace is restricted to those with the ADMIN role.
  ("get_profile", "1"): admin_users_get_profile_v1,
  ("set_credits", "1"): admin_users_set_credits_v1,
  ("reset_display", "1"): admin_users_reset_display_v1,
  ("enable_storage", "1"): admin_users_enable_storage_v1
}

