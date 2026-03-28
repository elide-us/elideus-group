from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateWorkflowRunParams,
  CreateWorkflowRunStepParams,
  GetActiveWorkflowParams,
  GetWorkflowRunParams,
  ListWorkflowsParams,
  ListWorkflowRunStepsParams,
  ListWorkflowRunsParams,
  ListWorkflowStepsParams,
  UpdateWorkflowRunParams,
  UpdateWorkflowRunStepParams,
)


def get_active_workflow_request(params: GetActiveWorkflowParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:get_active_workflow:1", payload=params.model_dump())


def list_workflows_request(params: ListWorkflowsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflows:1", payload=params.model_dump())


def list_workflow_steps_request(params: ListWorkflowStepsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflow_steps:1", payload=params.model_dump())


def create_workflow_run_request(params: CreateWorkflowRunParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:create_workflow_run:1", payload=params.model_dump())


def get_workflow_run_request(params: GetWorkflowRunParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:get_workflow_run:1", payload=params.model_dump())


def list_workflow_runs_request(params: ListWorkflowRunsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflow_runs:1", payload=params.model_dump())


def update_workflow_run_request(params: UpdateWorkflowRunParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:update_workflow_run:1", payload=params.model_dump(exclude_unset=True))


def create_workflow_run_step_request(params: CreateWorkflowRunStepParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:create_workflow_run_step:1", payload=params.model_dump())


def update_workflow_run_step_request(params: UpdateWorkflowRunStepParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:update_workflow_run_step:1", payload=params.model_dump(exclude_unset=True))


def list_workflow_run_steps_request(params: ListWorkflowRunStepsParams) -> DBRequest:
  return DBRequest(op="db:system:workflows:list_workflow_run_steps:1", payload=params.model_dump())
