from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CountActiveRunsByWorkflowNameParams,
  CreateWorkflowRunActionParams,
  CreateWorkflowRunParams,
  GetActiveWorkflowParams,
  GetWorkflowRunParams,
  ListWorkflowActionsParams,
  ListWorkflowRunActionsParams,
  ListWorkflowRunsParams,
  ListWorkflowsParams,
  UpdateWorkflowRunActionParams,
  UpdateWorkflowRunParams,
)


def get_active_workflow_request(params: GetActiveWorkflowParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:get_active_workflow:1", payload=params.model_dump())


def count_active_runs_by_workflow_name_request(params: CountActiveRunsByWorkflowNameParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:count_active_runs_by_workflow_name:1", payload=params.model_dump())


def list_workflows_request(params: ListWorkflowsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflows:1", payload=params.model_dump())


def list_workflow_actions_request(params: ListWorkflowActionsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflow_actions:1", payload=params.model_dump())


def create_workflow_run_request(params: CreateWorkflowRunParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:create_workflow_run:1", payload=params.model_dump())


def get_workflow_run_request(params: GetWorkflowRunParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:get_workflow_run:1", payload=params.model_dump())


def list_workflow_runs_request(params: ListWorkflowRunsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflow_runs:1", payload=params.model_dump())


def update_workflow_run_request(params: UpdateWorkflowRunParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:update_workflow_run:1", payload=params.model_dump(exclude_unset=True))


def create_workflow_run_action_request(params: CreateWorkflowRunActionParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:create_workflow_run_action:1", payload=params.model_dump())


def update_workflow_run_action_request(params: UpdateWorkflowRunActionParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:update_workflow_run_action:1", payload=params.model_dump(exclude_unset=True))


def list_workflow_run_actions_request(params: ListWorkflowRunActionsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflow_run_actions:1", payload=params.model_dump())
