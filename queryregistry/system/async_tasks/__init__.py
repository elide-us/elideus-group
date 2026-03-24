from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateTaskEventParams,
  CreateTaskParams,
  GetTaskParams,
  ListTaskEventsParams,
  ListTasksParams,
  UpdateTaskParams,
)


def create_task_request(params: CreateTaskParams) -> DBRequest:
  return DBRequest(op="db:system:async_tasks:create_task:1", payload=params.model_dump())


def get_task_request(params: GetTaskParams) -> DBRequest:
  return DBRequest(op="db:system:async_tasks:get_task:1", payload=params.model_dump())


def list_tasks_request(params: ListTasksParams) -> DBRequest:
  return DBRequest(op="db:system:async_tasks:list_tasks:1", payload=params.model_dump())


def update_task_request(params: UpdateTaskParams) -> DBRequest:
  return DBRequest(op="db:system:async_tasks:update_task:1", payload=params.model_dump(exclude_unset=True))


def create_task_event_request(params: CreateTaskEventParams) -> DBRequest:
  return DBRequest(op="db:system:async_tasks:create_task_event:1", payload=params.model_dump())


def list_task_events_request(params: ListTaskEventsParams) -> DBRequest:
  return DBRequest(op="db:system:async_tasks:list_task_events:1", payload=params.model_dump())
