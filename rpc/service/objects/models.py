from pydantic import BaseModel, ConfigDict


class ServiceObjectsReadChildrenParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  categoryGuid: str
  tableGuid: str | None = None


class ServiceObjectsReadDetailParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  tableGuid: str
  maxRows: int = 100


class ServiceObjectsUpsertDatabaseTableParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str | None = None
  name: str
  schema: str


class ServiceObjectsDeleteDatabaseTableParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str


class ServiceObjectsUpsertDatabaseColumnParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str | None = None
  tableGuid: str
  typeGuid: str
  name: str
  ordinal: int
  isNullable: bool
  isPrimaryKey: bool
  isIdentity: bool
  defaultValue: str | None = None
  maxLength: int | None = None


class ServiceObjectsDeleteDatabaseColumnParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str
