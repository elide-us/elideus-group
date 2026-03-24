from .services import (
  finance_staging_account_map_delete_v1,
  finance_staging_account_map_list_v1,
  finance_staging_account_map_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_staging_account_map_list_v1,
  ("upsert", "1"): finance_staging_account_map_upsert_v1,
  ("delete", "1"): finance_staging_account_map_delete_v1,
}
