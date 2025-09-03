from .services import (
  account_user_get_profile_v1,
  account_user_set_credits_v1,
  account_user_reset_display_v1,
  account_user_enable_storage_v1,
  account_user_check_storage_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_profile", "1"): account_user_get_profile_v1,
  ("set_credits", "1"): account_user_set_credits_v1,
  ("reset_display", "1"): account_user_reset_display_v1,
  ("enable_storage", "1"): account_user_enable_storage_v1,
  ("check_storage", "1"): account_user_check_storage_v1,
}
