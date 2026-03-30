from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  count_active_runs_by_workflow_name_v1,
  create_workflow_run_action_v1,
  create_workflow_run_v1,
  get_active_workflow_v1,
  get_workflow_run_v1,
  list_workflow_actions_v1,
  list_workflow_run_actions_v1,
  list_workflow_runs_v1,
  list_workflows_v1,
  update_workflow_run_action_v1,
  update_workflow_run_v1,
)

DISPATCHERS = {
  ("get_active_workflow", "1"): get_active_workflow_v1,
  ("count_active_runs_by_workflow_name", "1"): count_active_runs_by_workflow_name_v1,
  ("list_workflows", "1"): list_workflows_v1,
  ("list_workflow_actions", "1"): list_workflow_actions_v1,
  ("create_workflow_run", "1"): create_workflow_run_v1,
  ("get_workflow_run", "1"): get_workflow_run_v1,
  ("list_workflow_runs", "1"): list_workflow_runs_v1,
  ("update_workflow_run", "1"): update_workflow_run_v1,
  ("create_workflow_run_action", "1"): create_workflow_run_action_v1,
  ("update_workflow_run_action", "1"): update_workflow_run_action_v1,
  ("list_workflow_run_actions", "1"): list_workflow_run_actions_v1,
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
