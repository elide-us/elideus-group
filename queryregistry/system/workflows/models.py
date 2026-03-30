from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GetActiveWorkflowParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str


class CountActiveRunsByWorkflowNameParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str


class ListWorkflowsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  status: int | None = None


class ListWorkflowActionsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  workflows_guid: str


class CreateWorkflowRunParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  workflows_guid: str
  status: int = 0
  payload: str | None = None
  context: str | None = None
  current_action: str | None = None
  action_index: int = 0
  error: str | None = None
  trigger_type: int | None = None
  trigger_ref: str | None = None
  result: str | None = None
  created_by: str | None = None
  started_on: str | None = None
  ended_on: str | None = None


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
  current_action: str | None = None
  action_index: int | None = None
  error: str | None = None
  trigger_type: int | None = None
  trigger_ref: str | None = None
  result: str | None = None
  started_on: str | None = None
  ended_on: str | None = None


class CreateWorkflowRunActionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  runs_recid: int
  actions_guid: str
  status: int = 0
  input: str | None = None
  output: str | None = None
  error: str | None = None
  sequence: int = 0
  retry_count: int = 0
  external_ref: str | None = None
  poll_interval_seconds: int | None = None
  started_on: str | None = None
  ended_on: str | None = None


class UpdateWorkflowRunActionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int | None = None
  output: str | None = None
  error: str | None = None
  retry_count: int | None = None
  external_ref: str | None = None
  poll_interval_seconds: int | None = None
  started_on: str | None = None
  ended_on: str | None = None


class ListWorkflowRunActionsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  runs_recid: int
