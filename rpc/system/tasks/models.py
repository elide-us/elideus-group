from pydantic import BaseModel, Field


class SystemTaskItem1(BaseModel):
  recid: int
  guid: str
  handler_type: str
  handler_name: str
  payload: dict | None = None
  status: int
  result: dict | list | str | None = None
  error: str | None = None
  current_step: str | None = None
  step_index: int = 0
  max_retries: int = 0
  retry_count: int = 0
  poll_interval_seconds: int | None = None
  timeout_seconds: int | None = None
  timeout_at: str | None = None
  external_id: str | None = None
  source_type: str | None = None
  source_id: str | None = None
  created_by: str | None = None
  created_on: str | None = None
  modified_on: str | None = None


class SystemTaskList1(BaseModel):
  tasks: list[SystemTaskItem1]


class SystemTaskListRequest1(BaseModel):
  status: int | None = None
  handler_type: str | None = None
  handler_name: str | None = None


class SystemTaskGetRequest1(BaseModel):
  guid: str


class SystemTaskSubmitRequest1(BaseModel):
  handler_name: str
  payload: dict = Field(default_factory=dict)
  source_type: str | None = "rpc"
  source_id: str | None = None
  timeout_seconds: int | None = None
  poll_interval_seconds: int | None = None
  max_retries: int = 0


class SystemTaskCancelRequest1(BaseModel):
  guid: str


class SystemTaskRetryRequest1(BaseModel):
  guid: str


class SystemTaskEventsRequest1(BaseModel):
  guid: str


class SystemTaskEventItem1(BaseModel):
  recid: int
  tasks_recid: int
  element_event_type: str
  element_step_name: str | None = None
  element_detail: str | None = None
  element_created_on: str


class SystemTaskEventsList1(BaseModel):
  events: list[SystemTaskEventItem1]
