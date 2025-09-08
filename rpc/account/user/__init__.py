from .services import (
  account_user_get_displayname_v1,
  account_user_get_credits_v1,
  account_user_set_credits_v1,
  account_user_reset_display_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_displayname", "1"): account_user_get_displayname_v1,
  ("get_credits", "1"): account_user_get_credits_v1,
  ("set_credits", "1"): account_user_set_credits_v1,
  ("reset_display", "1"): account_user_reset_display_v1,
}
