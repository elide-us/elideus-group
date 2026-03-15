from pydantic import BaseModel


class BatchJobItem1(BaseModel):
  recid: int | None = None
  name: str
  description: str | None = None
  class_path: str
  parameters: str | None = None
  cron: str
  recurrence_type: int = 0
  run_count_limit: int | None = None
  run_until: str | None = None
  total_runs: int = 0
  is_enabled: bool = True
  last_run: str | None = None
  next_run: str | None = None
  status: int = 0


class BatchJobList1(BaseModel):
  jobs: list[BatchJobItem1]


class BatchJobGet1(BaseModel):
  recid: int


class BatchJobUpsert1(BatchJobItem1):
  pass


class BatchJobDelete1(BaseModel):
  recid: int


class BatchJobListHistory1(BaseModel):
  jobs_recid: int


class BatchJobRunNow1(BaseModel):
  recid: int


class BatchJobHistoryItem1(BaseModel):
  recid: int | None = None
  jobs_recid: int
  started_on: str | None = None
  ended_on: str | None = None
  status: int = 1
  error: str | None = None
  result: str | None = None


class BatchJobHistoryList1(BaseModel):
  history: list[BatchJobHistoryItem1]
