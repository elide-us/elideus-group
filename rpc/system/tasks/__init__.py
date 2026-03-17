from .services import (
  system_tasks_cancel_v1,
  system_tasks_events_v1,
  system_tasks_get_v1,
  system_tasks_list_v1,
  system_tasks_retry_v1,
  system_tasks_submit_v1,
)

DISPATCHERS = {
  ("list", "1"): system_tasks_list_v1,
  ("get", "1"): system_tasks_get_v1,
  ("submit", "1"): system_tasks_submit_v1,
  ("cancel", "1"): system_tasks_cancel_v1,
  ("retry", "1"): system_tasks_retry_v1,
  ("events", "1"): system_tasks_events_v1,
}
