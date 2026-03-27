from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_workflow_run_step_v1,
  create_workflow_run_v1,
  get_active_workflow_v1,
  get_workflow_run_v1,
  list_workflow_run_steps_v1,
  list_workflow_runs_v1,
  list_workflow_steps_v1,
  update_workflow_run_step_v1,
  update_workflow_run_v1,
)

DISPATCHERS = {
  ("get_active_workflow", "1"): get_active_workflow_v1,
  ("list_workflow_steps", "1"): list_workflow_steps_v1,
  ("create_workflow_run", "1"): create_workflow_run_v1,
  ("get_workflow_run", "1"): get_workflow_run_v1,
  ("list_workflow_runs", "1"): list_workflow_runs_v1,
  ("update_workflow_run", "1"): update_workflow_run_v1,
  ("create_workflow_run_step", "1"): create_workflow_run_step_v1,
  ("update_workflow_run_step", "1"): update_workflow_run_step_v1,
  ("list_workflow_run_steps", "1"): list_workflow_run_steps_v1,
}


async def handle_workflows_request(
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
    detail="Unknown system workflows operation",
  )
