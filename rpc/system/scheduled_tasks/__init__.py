"""System scheduled tasks RPC namespace.

Requires ROLE_SYSTEM_ADMIN.
"""

from .services import (
  system_scheduled_tasks_get_v1,
  system_scheduled_tasks_list_history_v1,
  system_scheduled_tasks_list_v1,
  system_scheduled_tasks_run_now_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): system_scheduled_tasks_list_v1,
  ("get", "1"): system_scheduled_tasks_get_v1,
  ("list_history", "1"): system_scheduled_tasks_list_history_v1,
  ("run_now", "1"): system_scheduled_tasks_run_now_v1,
}
