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
  source: str
  scope: str | None = None
  metric: str
  period_start: str
  period_end: str
  row_count: int
  status: int
  error: str | None = None
  created_on: str
  modified_on: str


class StagingImportList1(BaseModel):
  imports: list[StagingImportItem1]


class StagingListDetails1(BaseModel):
  imports_recid: int

