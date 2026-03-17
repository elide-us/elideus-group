from .services import (
  finance_numbers_delete_v1,
  finance_numbers_get_v1,
  finance_numbers_list_v1,
  finance_numbers_next_number_v1,
  finance_numbers_shift_v1,
  finance_numbers_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_numbers_list_v1,
  ("get", "1"): finance_numbers_get_v1,
  ("upsert", "1"): finance_numbers_upsert_v1,
  ("delete", "1"): finance_numbers_delete_v1,
  ("next_number", "1"): finance_numbers_next_number_v1,
  ("shift", "1"): finance_numbers_shift_v1,
}
