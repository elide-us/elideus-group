from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GetActiveWorkflowParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str


class ListWorkflowStepsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  workflows_guid: str


class CreateWorkflowRunParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  workflows_guid: str
  status: int = 0
  payload: str | None = None
  context: str | None = None
  current_step: str | None = None
  step_index: int = 0
  error: str | None = None
  source_type: str | None = None
  source_id: str | None = None
  created_by: str | None = None
  started_on: str | None = None
  ended_on: str | None = None
  timeout_at: str | None = None


class GetWorkflowRunParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class ListWorkflowRunsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  workflows_guid: str | None = None
  status: int | None = None


class UpdateWorkflowRunParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int | None = None
  context: str | None = None
  current_step: str | None = None
  step_index: int | None = None
  error: str | None = None
  started_on: str | None = None
  ended_on: str | None = None


class CreateWorkflowRunStepParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  runs_recid: int
  steps_guid: str
  status: int = 0
  disposition: str
  input: str | None = None
  output: str | None = None
  error: str | None = None
  started_on: str | None = None
  ended_on: str | None = None


class UpdateWorkflowRunStepParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int | None = None
  output: str | None = None
  error: str | None = None
  started_on: str | None = None
  ended_on: str | None = None


class ListWorkflowRunStepsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  runs_recid: int
