from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_task_event_v1,
  create_task_v1,
  get_task_v1,
  list_task_events_v1,
  list_tasks_v1,
  update_task_v1,
)

DISPATCHERS = {
  ("create_task", "1"): create_task_v1,
  ("get_task", "1"): get_task_v1,
  ("list_tasks", "1"): list_tasks_v1,
  ("update_task", "1"): update_task_v1,
  ("create_task_event", "1"): create_task_event_v1,
  ("list_task_events", "1"): list_task_events_v1,
}


async def handle_async_tasks_request(
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
    detail="Unknown system async_tasks operation",
  )
