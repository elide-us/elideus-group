from .services import (
  finance_pipeline_config_delete_v1,
  finance_pipeline_config_get_v1,
  finance_pipeline_config_list_v1,
  finance_pipeline_config_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_pipeline_config_list_v1,
  ("get", "1"): finance_pipeline_config_get_v1,
  ("upsert", "1"): finance_pipeline_config_upsert_v1,
  ("delete", "1"): finance_pipeline_config_delete_v1,
}
