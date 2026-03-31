from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_scheduled_task_history_v1,
  get_task_v1,
  get_workflow_name_by_guid_v1,
  list_all_tasks_v1,
  list_enabled_due_tasks_v1,
  list_task_history_v1,
  update_scheduled_task_v1,
)

DISPATCHERS = {
  ("list_enabled_due_tasks", "1"): list_enabled_due_tasks_v1,
  ("list_all_tasks", "1"): list_all_tasks_v1,
  ("get_task", "1"): get_task_v1,
  ("list_task_history", "1"): list_task_history_v1,
  ("update_scheduled_task", "1"): update_scheduled_task_v1,
  ("create_scheduled_task_history", "1"): create_scheduled_task_history_v1,
  ("get_workflow_name_by_guid", "1"): get_workflow_name_by_guid_v1,
}


async def handle_scheduled_tasks_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown system scheduled_tasks operation",
  )
