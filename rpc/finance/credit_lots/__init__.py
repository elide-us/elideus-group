from .services import (
  finance_credit_lots_consume_v1,
  finance_credit_lots_create_v1,
  finance_credit_lots_expire_v1,
  finance_credit_lots_get_v1,
  finance_credit_lots_list_by_user_v1,
  finance_credit_lots_list_events_v1,
  finance_credit_lots_wallet_balance_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_by_user", "1"): finance_credit_lots_list_by_user_v1,
  ("get", "1"): finance_credit_lots_get_v1,
  ("create", "1"): finance_credit_lots_create_v1,
  ("consume", "1"): finance_credit_lots_consume_v1,
  ("expire", "1"): finance_credit_lots_expire_v1,
  ("list_events", "1"): finance_credit_lots_list_events_v1,
  ("wallet_balance", "1"): finance_credit_lots_wallet_balance_v1,
}
