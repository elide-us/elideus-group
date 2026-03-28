from pydantic import BaseModel, Field


# --- Workflow definition models ---

class SystemWorkflowItem1(BaseModel):
  guid: str
  name: str
  description: str | None = None
  version: int
  status: int
  step_count: int | None = None
  created_on: str | None = None
  modified_on: str | None = None


class SystemWorkflowList1(BaseModel):
  workflows: list[SystemWorkflowItem1]


class SystemWorkflowListRequest1(BaseModel):
  status: int | None = None


class SystemWorkflowGetRequest1(BaseModel):
  name: str


class SystemWorkflowStepItem1(BaseModel):
  guid: str
  name: str
  description: str | None = None
  step_type: str
  disposition: str
  class_path: str
  sequence: int
  is_optional: bool = False
  timeout_seconds: int | None = None
  config: str | None = None


class SystemWorkflowDetail1(BaseModel):
  guid: str
  name: str
  description: str | None = None
  version: int
  status: int
  steps: list[SystemWorkflowStepItem1]


# --- Workflow run models ---

class SystemWorkflowRunItem1(BaseModel):
  recid: int
  guid: str
  workflows_guid: str
  status: int
  payload: dict | None = None
  context: dict | None = None
  current_step: str | None = None
  step_index: int = 0
  error: str | None = None
  source_type: str | None = None
  source_id: str | None = None
  created_by: str | None = None
  started_on: str | None = None
  ended_on: str | None = None
  timeout_at: str | None = None
  created_on: str | None = None
  modified_on: str | None = None


class SystemWorkflowRunList1(BaseModel):
  runs: list[SystemWorkflowRunItem1]


class SystemWorkflowRunListRequest1(BaseModel):
  status: int | None = None
  workflows_guid: str | None = None


class SystemWorkflowRunGetRequest1(BaseModel):
  guid: str


class SystemWorkflowRunSubmitRequest1(BaseModel):
  workflow_name: str
  payload: dict = Field(default_factory=dict)
  source_type: str | None = "rpc"
  source_id: str | None = None
  timeout_seconds: int | None = None


class SystemWorkflowRunCancelRequest1(BaseModel):
  guid: str


class SystemWorkflowRunRollbackRequest1(BaseModel):
  guid: str


# --- Run step models ---

class SystemWorkflowRunStepItem1(BaseModel):
  recid: int
  guid: str
  runs_recid: int
  steps_guid: str
  status: int
  disposition: str
  input: dict | None = None
  output: dict | None = None
  error: str | None = None
  started_on: str | None = None
  ended_on: str | None = None
  created_on: str | None = None
  modified_on: str | None = None


class SystemWorkflowRunStepList1(BaseModel):
  steps: list[SystemWorkflowRunStepItem1]


class SystemWorkflowRunStepListRequest1(BaseModel):
  run_guid: str
