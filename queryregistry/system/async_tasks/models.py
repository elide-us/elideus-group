from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CreateTaskParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  handler_type: str
  handler_name: str
  payload: str | None = None
  status: int = 0
  max_retries: int = 0
  retry_count: int = 0
  poll_interval_seconds: int | None = None
  timeout_seconds: int | None = None
  timeout_at: str | None = None
  external_id: str | None = None
  source_type: str | None = None
  source_id: str | None = None
  created_by: str | None = None


class GetTaskParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class ListTasksParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  status: int | None = None
  handler_type: str | None = None
  handler_name: str | None = None


class UpdateTaskParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int | None = None
  result: dict | list | str | None = None
  error: str | None = None
  current_step: str | None = None
  step_index: int | None = None
  retry_count: int | None = None
  poll_interval_seconds: int | None = None
  timeout_seconds: int | None = None
  timeout_at: str | None = None
  external_id: str | None = None


class CreateTaskEventParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  tasks_recid: int
  event_type: str
  step_name: str | None = None
  detail: str | None = None


class ListTaskEventsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  tasks_recid: int
