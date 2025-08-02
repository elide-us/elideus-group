from .services import (account_users_get_profile_v1,
                       account_users_set_display_v1,
                       account_users_set_credits_v1, 
                       account_users_enable_storage_v1)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_profile", "1"): account_users_get_profile_v1,
  ("set_creits", "1"): account_users_set_credits_v1,
  ("set_display", "1"): account_users_set_display_v1,
  ("enable_storage", "1"): account_users_enable_storage_v1
}

