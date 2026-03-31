"""System workflows RPC namespace.

Requires ROLE_SYSTEM_ADMIN.
"""

from .services import (
  system_workflows_cancel_run_v1,
  system_workflows_get_run_v1,
  system_workflows_get_workflow_v1,
  system_workflows_list_run_actions_v1,
  system_workflows_list_runs_v1,
  system_workflows_list_workflows_v1,
  system_workflows_resume_run_v1,
  system_workflows_retry_run_action_v1,
  system_workflows_rollback_run_v1,
  system_workflows_submit_run_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_workflows", "1"): system_workflows_list_workflows_v1,
  ("get_workflow", "1"): system_workflows_get_workflow_v1,
  ("list_runs", "1"): system_workflows_list_runs_v1,
  ("get_run", "1"): system_workflows_get_run_v1,
  ("submit_run", "1"): system_workflows_submit_run_v1,
  ("cancel_run", "1"): system_workflows_cancel_run_v1,
  ("rollback_run", "1"): system_workflows_rollback_run_v1,
  ("resume_run", "1"): system_workflows_resume_run_v1,
  ("retry_run_action", "1"): system_workflows_retry_run_action_v1,
  ("list_run_actions", "1"): system_workflows_list_run_actions_v1,
}
