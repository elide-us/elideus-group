from rpc.account.user import services as account_user_services


DISPATCHERS: dict[tuple[str, str], callable] = {
  # This module is used by moderators to manage user accounts.
  # This namespace is restricted to those with the SUPPORT role.
  ("get_displayname", "1"): account_user_services.account_user_get_displayname_v1,
  ("get_credits", "1"): account_user_services.account_user_get_credits_v1,
  ("set_credits", "1"): account_user_services.account_user_set_credits_v1,
  ("reset_display", "1"): account_user_services.account_user_reset_display_v1,
}

