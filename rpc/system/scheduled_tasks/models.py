from pydantic import BaseModel


class ScheduledTaskItem1(BaseModel):
  recid: int
  name: str
  description: str | None = None
  workflows_guid: str
  payload_template: str | None = None
  cron: str
  recurrence_type: int = 0
  run_count_limit: int | None = None
  run_until: str | None = None
  total_runs: int = 0
  status: int = 1
  last_run: str | None = None
  next_run: str | None = None
  created_on: str | None = None
  modified_on: str | None = None


class ScheduledTaskList1(BaseModel):
  tasks: list[ScheduledTaskItem1]


class ScheduledTaskGetRequest1(BaseModel):
  recid: int


class ScheduledTaskHistoryItem1(BaseModel):
  recid: int
  tasks_recid: int
  runs_recid: int | None = None
  fired_on: str | None = None
  error: str | None = None
  created_on: str | None = None


class ScheduledTaskHistoryList1(BaseModel):
  history: list[ScheduledTaskHistoryItem1]


class ScheduledTaskListHistoryRequest1(BaseModel):
  tasks_recid: int


class ScheduledTaskRunNowRequest1(BaseModel):
  recid: int
