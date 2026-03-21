from pydantic import BaseModel


class FinancePipelineConfigItem1(BaseModel):
  recid: int | None = None
  element_pipeline: str
  element_key: str
  element_value: str
  element_description: str | None = None
  element_status: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class FinancePipelineConfigList1(BaseModel):
  configs: list[FinancePipelineConfigItem1]


class FinancePipelineConfigFilter1(BaseModel):
  element_pipeline: str | None = None


class FinancePipelineConfigGet1(BaseModel):
  element_pipeline: str
  element_key: str


class FinancePipelineConfigUpsert1(BaseModel):
  recid: int | None = None
  element_pipeline: str
  element_key: str
  element_value: str
  element_description: str | None = None
  element_status: int = 1


class FinancePipelineConfigDelete1(BaseModel):
  recid: int


class FinancePipelineConfigDeleteResult1(BaseModel):
  recid: int
  deleted: bool
