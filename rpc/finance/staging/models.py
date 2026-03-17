from pydantic import BaseModel


class StagingImport1(BaseModel):
  period_start: str
  period_end: str
  metric: str = "ActualCost"


class StagingImportResult1(BaseModel):
  import_recid: int
  status: str
  row_count: int


class StagingImportItem1(BaseModel):
  recid: int
  element_source: str
  element_scope: str | None = None
  element_metric: str
  element_period_start: str
  element_period_end: str
  element_row_count: int
  element_status: int
  element_error: str | None = None
  element_created_on: str | None = None
  element_modified_on: str | None = None


class StagingImportList1(BaseModel):
  imports: list[StagingImportItem1]


class StagingListDetails1(BaseModel):
  imports_recid: int



class StagingDeleteImport1(BaseModel):
  imports_recid: int


class StagingDeleteResult1(BaseModel):
  imports_recid: int
  deleted: bool


class StagingPromote1(BaseModel):
  imports_recid: int


class StagingPromoteResult1(BaseModel):
  task_guid: str

