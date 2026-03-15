from .services import (
  system_batch_jobs_delete_v1,
  system_batch_jobs_get_v1,
  system_batch_jobs_list_history_v1,
  system_batch_jobs_list_v1,
  system_batch_jobs_run_now_v1,
  system_batch_jobs_upsert_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): system_batch_jobs_list_v1,
  ("get", "1"): system_batch_jobs_get_v1,
  ("upsert", "1"): system_batch_jobs_upsert_v1,
  ("delete", "1"): system_batch_jobs_delete_v1,
  ("list_history", "1"): system_batch_jobs_list_history_v1,
  ("run_now", "1"): system_batch_jobs_run_now_v1,
}
