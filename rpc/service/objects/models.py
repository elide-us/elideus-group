from pydantic import BaseModel, ConfigDict


class ServiceObjectsReadChildrenParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  categoryGuid: str
  tableGuid: str | None = None


class ServiceObjectsReadDetailParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  tableGuid: str
  maxRows: int = 100
