from pydantic import BaseModel, Field


# --- Workflow definition models ---

class SystemWorkflowItem1(BaseModel):
  guid: str
  name: str
  description: str | None = None
  version: int
  status: int
  is_active: bool | None = None
  max_concurrency: int | None = None
  stall_threshold_seconds: int | None = None
  created_on: str | None = None
  modified_on: str | None = None


class SystemWorkflowList1(BaseModel):
  workflows: list[SystemWorkflowItem1]


class SystemWorkflowListRequest1(BaseModel):
  status: int | None = None


class SystemWorkflowGetRequest1(BaseModel):
  name: str


class SystemWorkflowActionItem1(BaseModel):
  guid: str
  workflows_guid: str | None = None
  name: str
  description: str | None = None
  functions_guid: str | None = None
  dispositions_recid: int | None = None
  rollback_functions_guid: str | None = None
  sequence: int
  is_optional: bool = False
  timeout_seconds: int | None = None
  config: str | None = None
  is_active: bool | None = None
  module_attr: str | None = None
  method_name: str | None = None
  disposition_name: str | None = None


class SystemWorkflowDetail1(BaseModel):
  guid: str
  name: str
  description: str | None = None
  version: int
  status: int
  actions: list[SystemWorkflowActionItem1]


# --- Workflow run models ---

class SystemWorkflowRunItem1(BaseModel):
  recid: int
  guid: str
  workflows_guid: str
  status: int
  payload: dict | None = None
  context: dict | None = None
  current_action: str | None = None
  action_index: int = 0
  error: str | None = None
  trigger_type: int | None = None
  trigger_ref: str | None = None
  result: dict | None = None
  created_by: str | None = None
  started_on: str | None = None
  ended_on: str | None = None
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
  trigger_type: int = 2
  trigger_ref: str | None = None


class SystemWorkflowRunCancelRequest1(BaseModel):
  guid: str


class SystemWorkflowRunRollbackRequest1(BaseModel):
  guid: str


class SystemWorkflowRunResumeRequest1(BaseModel):
  guid: str


class SystemWorkflowRunRetryActionRequest1(BaseModel):
  run_action_guid: str


# --- Run action models ---

class SystemWorkflowRunActionItem1(BaseModel):
  recid: int
  guid: str
  runs_recid: int
  actions_guid: str
  status: int
  input: dict | None = None
  output: dict | None = None
  error: str | None = None
  sequence: int | None = None
  retry_count: int = 0
  external_ref: str | None = None
  poll_interval_seconds: int | None = None
  started_on: str | None = None
  ended_on: str | None = None
  created_on: str | None = None
  modified_on: str | None = None


class SystemWorkflowRunActionList1(BaseModel):
  actions: list[SystemWorkflowRunActionItem1]


class SystemWorkflowRunActionListRequest1(BaseModel):
  run_guid: str


class SystemWorkflowScanStallsRequest1(BaseModel):
  payload: dict = Field(default_factory=dict)


class SystemWorkflowScanStallsResponse1(BaseModel):
  context: dict = Field(default_factory=dict)
