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


class ServiceObjectsUpsertTypeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str | None = None
  name: str
  mssqlType: str
  postgresqlType: str | None = None
  mysqlType: str | None = None
  pythonType: str
  typescriptType: str
  jsonType: str
  odbcTypeCode: int | None = None
  maxLength: int | None = None
  notes: str | None = None


class ServiceObjectsDeleteTypeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str


class ServiceObjectsGetTypeControlsParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  typeGuid: str


class ServiceObjectsGetModuleMethodsParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  moduleGuid: str


class ServiceObjectsUpsertModuleParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str
  description: str | None = None
  isActive: bool


class ServiceObjectsUpsertModuleMethodParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str | None = None
  moduleGuid: str
  name: str
  description: str | None = None
  isActive: bool


class ServiceObjectsDeleteModuleMethodParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str


class ServiceObjectsGetMethodContractParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  methodGuid: str
