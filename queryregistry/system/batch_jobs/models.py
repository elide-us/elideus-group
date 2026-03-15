"""System batch jobs query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "BatchJobHistoryRecord",
  "BatchJobRecord",
  "CreateHistoryParams",
  "DeleteJobParams",
  "GetJobParams",
  "ListHistoryParams",
  "ListJobsParams",
  "UpdateHistoryParams",
  "UpdateJobStatusParams",
  "UpsertJobParams",
]


class ListJobsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class GetJobParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class UpsertJobParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  name: str
  description: str | None = None
  class_path: str
  parameters: str | None = None
  cron: str
  recurrence_type: int = 0
  run_count_limit: int | None = None
  run_until: str | None = None
  is_enabled: bool = True


class DeleteJobParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class ListHistoryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  jobs_recid: int


class CreateHistoryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  jobs_recid: int


class UpdateHistoryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int
  error: str | None = None
  result: str | None = None


class UpdateJobStatusParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int
  total_runs: int | None = None
  last_run: str | None = None
  next_run: str | None = None


class BatchJobRecord(TypedDict):
  recid: int
  element_name: str
  element_description: str | None
  element_class: str
  element_parameters: str | None
  element_cron: str
  element_recurrence_type: int
  element_run_count_limit: int | None
  element_run_until: str | None
  element_total_runs: int
  element_is_enabled: bool
  element_last_run: str | None
  element_next_run: str | None
  element_status: int
  element_created_on: str
  element_modified_on: str


class BatchJobHistoryRecord(TypedDict):
  recid: int
  jobs_recid: int
  element_started_on: str
  element_ended_on: str | None
  element_status: int
  element_error: str | None
  element_result: str | None
  element_created_on: str
