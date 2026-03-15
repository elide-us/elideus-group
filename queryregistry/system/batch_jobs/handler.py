"""System batch jobs handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_history_v1,
  delete_job_v1,
  get_job_v1,
  list_history_v1,
  list_jobs_v1,
  update_history_v1,
  update_job_status_v1,
  upsert_job_v1,
)

__all__ = ["handle_batch_jobs_request"]

DISPATCHERS = {
  ("list_jobs", "1"): list_jobs_v1,
  ("get_job", "1"): get_job_v1,
  ("upsert_job", "1"): upsert_job_v1,
  ("delete_job", "1"): delete_job_v1,
  ("list_history", "1"): list_history_v1,
  ("create_history", "1"): create_history_v1,
  ("update_history", "1"): update_history_v1,
  ("update_job_status", "1"): update_job_status_v1,
}


async def handle_batch_jobs_request(
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
    detail="Unknown system batch_jobs operation",
  )
