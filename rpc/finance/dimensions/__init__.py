from .services import (
  finance_dimensions_delete_v1,
  finance_dimensions_get_v1,
  finance_dimensions_list_by_name_v1,
  finance_dimensions_list_v1,
  finance_dimensions_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_dimensions_list_v1,
  ("list_by_name", "1"): finance_dimensions_list_by_name_v1,
  ("get", "1"): finance_dimensions_get_v1,
  ("upsert", "1"): finance_dimensions_upsert_v1,
  ("delete", "1"): finance_dimensions_delete_v1,
}
