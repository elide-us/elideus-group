from pydantic import BaseModel, field_validator


class StagingImport1(BaseModel):
  period_start: str
  period_end: str
  metric: str = "ActualCost"


class StagingImportResult1(BaseModel):
  import_recid: int
  status: str
  row_count: int


class StagingImportInvoices1(BaseModel):
  period_start: str
  period_end: str


class StagingImportInvoicesResult1(BaseModel):
  import_recid: int
  status: str
  invoice_count: int
  skipped_count: int


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



class StagingLineItem1(BaseModel):
  recid: int
  imports_recid: int
  vendors_recid: int
  vendor_name: str | None = None
  element_date: str | None = None
  element_service: str | None = None
  element_category: str | None = None
  element_description: str | None = None
  element_quantity: str | None = None
  element_unit_price: str | None = None
  element_amount: str
  element_currency: str | None = None
  element_raw_json: str | None = None
  element_created_on: str | None = None

  @field_validator("element_amount", "element_quantity", "element_unit_price", mode="before")
  @classmethod
  def coerce_numeric_to_str(cls, value):
    if value is None:
      return "0"
    return str(value)


class StagingLineItemList1(BaseModel):
  line_items: list[StagingLineItem1]
