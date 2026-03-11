from .services import (
  system_models_delete_model_v1,
  system_models_get_models_v1,
  system_models_upsert_model_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_models", "1"): system_models_get_models_v1,
  ("upsert_model", "1"): system_models_upsert_model_v1,
  ("delete_model", "1"): system_models_delete_model_v1,
}
