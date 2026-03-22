from .services import (
  finance_product_journal_config_activate_v1,
  finance_product_journal_config_approve_v1,
  finance_product_journal_config_close_v1,
  finance_product_journal_config_get_v1,
  finance_product_journal_config_list_v1,
  finance_product_journal_config_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_product_journal_config_list_v1,
  ("get", "1"): finance_product_journal_config_get_v1,
  ("upsert", "1"): finance_product_journal_config_upsert_v1,
  ("approve", "1"): finance_product_journal_config_approve_v1,
  ("activate", "1"): finance_product_journal_config_activate_v1,
  ("close", "1"): finance_product_journal_config_close_v1,
}
