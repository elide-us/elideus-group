from .services import finance_vendors_delete_v1, finance_vendors_list_v1, finance_vendors_upsert_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_vendors_list_v1,
  ("upsert", "1"): finance_vendors_upsert_v1,
  ("delete", "1"): finance_vendors_delete_v1,
}
