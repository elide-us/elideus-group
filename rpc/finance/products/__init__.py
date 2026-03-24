from .services import (
  finance_products_delete_v1,
  finance_products_get_v1,
  finance_products_list_v1,
  finance_products_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_products_list_v1,
  ("get", "1"): finance_products_get_v1,
  ("upsert", "1"): finance_products_upsert_v1,
  ("delete", "1"): finance_products_delete_v1,
}
