from pydantic import BaseModel


class FinanceStagingAccountMapItem1(BaseModel):
  recid: int | None = None
  vendors_recid: int | None = None
  vendor_name: str | None = None
  element_service_pattern: str
  element_meter_pattern: str | None = None
  accounts_guid: str
  account_number: str | None = None
  account_name: str | None = None
  element_priority: int = 0
  element_description: str | None = None
  element_status: int = 1


class FinanceStagingAccountMapList1(BaseModel):
  mappings: list[FinanceStagingAccountMapItem1]


class FinanceStagingAccountMapUpsert1(BaseModel):
  recid: int | None = None
  vendors_recid: int | None = None
  vendor_name: str | None = None
  element_service_pattern: str
  element_meter_pattern: str | None = None
  accounts_guid: str
  element_priority: int = 0
  element_description: str | None = None
  element_status: int = 1


class FinanceStagingAccountMapDelete1(BaseModel):
  recid: int


class FinanceStagingAccountMapDeleteResult1(BaseModel):
  recid: int
  deleted: bool
