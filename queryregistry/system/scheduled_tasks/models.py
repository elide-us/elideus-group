from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ListEnabledDueTasksParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  now: str


class UpdateScheduledTaskParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  total_runs: int | None = None
  last_run: str | None = None
  next_run: str | None = None
  status: int | None = None


class CreateScheduledTaskHistoryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  tasks_recid: int
  runs_recid: int | None = None
  error: str | None = None


class GetWorkflowNameByGuidParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class ListAllTasksParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class GetTaskParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class ListTaskHistoryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  tasks_recid: int
