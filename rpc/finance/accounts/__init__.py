from .services import (
  finance_accounts_delete_v1,
  finance_accounts_get_v1,
  finance_accounts_list_children_v1,
  finance_accounts_list_v1,
  finance_accounts_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_accounts_list_v1,
  ("get", "1"): finance_accounts_get_v1,
  ("upsert", "1"): finance_accounts_upsert_v1,
  ("delete", "1"): finance_accounts_delete_v1,
  ("list_children", "1"): finance_accounts_list_children_v1,
}
