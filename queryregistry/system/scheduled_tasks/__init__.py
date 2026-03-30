from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateScheduledTaskHistoryParams,
  GetWorkflowNameByGuidParams,
  ListEnabledDueTasksParams,
  UpdateScheduledTaskParams,
)


def list_enabled_due_tasks_request(params: ListEnabledDueTasksParams) -> DBRequest:
  return DBRequest(op="db:system:scheduled_tasks:list_enabled_due_tasks:1", payload=params.model_dump())


def update_scheduled_task_request(params: UpdateScheduledTaskParams) -> DBRequest:
  return DBRequest(op="db:system:scheduled_tasks:update_scheduled_task:1", payload=params.model_dump(exclude_unset=True))


def create_scheduled_task_history_request(params: CreateScheduledTaskHistoryParams) -> DBRequest:
  return DBRequest(op="db:system:scheduled_tasks:create_scheduled_task_history:1", payload=params.model_dump())


def get_workflow_name_by_guid_request(params: GetWorkflowNameByGuidParams) -> DBRequest:
  return DBRequest(op="db:system:scheduled_tasks:get_workflow_name_by_guid:1", payload=params.model_dump())
