from .services import (
  finance_ledgers_create_v1,
  finance_ledgers_delete_v1,
  finance_ledgers_get_v1,
  finance_ledgers_list_v1,
  finance_ledgers_update_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("create", "1"): finance_ledgers_create_v1,
  ("delete", "1"): finance_ledgers_delete_v1,
  ("get", "1"): finance_ledgers_get_v1,
  ("list", "1"): finance_ledgers_list_v1,
  ("update", "1"): finance_ledgers_update_v1,
}
