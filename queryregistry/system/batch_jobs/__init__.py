"""System batch jobs query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateHistoryParams,
  DeleteJobParams,
  GetJobParams,
  ListHistoryParams,
  ListJobsParams,
  UpdateHistoryParams,
  UpdateJobStatusParams,
  UpsertJobParams,
)

__all__ = [
  "create_history_request",
  "delete_job_request",
  "get_job_request",
  "list_history_request",
  "list_jobs_request",
  "update_history_request",
  "update_job_status_request",
  "upsert_job_request",
]


def list_jobs_request(params: ListJobsParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:list_jobs:1", payload=params.model_dump())


def get_job_request(params: GetJobParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:get_job:1", payload=params.model_dump())


def upsert_job_request(params: UpsertJobParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:upsert_job:1", payload=params.model_dump())


def delete_job_request(params: DeleteJobParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:delete_job:1", payload=params.model_dump())


def list_history_request(params: ListHistoryParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:list_history:1", payload=params.model_dump())


def create_history_request(params: CreateHistoryParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:create_history:1", payload=params.model_dump())


def update_history_request(params: UpdateHistoryParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:update_history:1", payload=params.model_dump())


def update_job_status_request(params: UpdateJobStatusParams) -> DBRequest:
  return DBRequest(op="db:system:batch_jobs:update_job_status:1", payload=params.model_dump())
