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


class ServiceObjectsGetPageTreeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  pageGuid: str


class ServiceObjectsListComponentsParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")


class ServiceObjectsGetComponentDetailParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  componentGuid: str


class ServiceObjectsUpsertComponentParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str
  description: str | None = None
  defaultTypeGuid: str | None = None


class ServiceObjectsCreateTreeNodeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  pageGuid: str
  parentGuid: str | None = None
  componentGuid: str
  label: str | None = None
  fieldBinding: str | None = None
  sequence: int = 0


class ServiceObjectsUpdateTreeNodeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str
  label: str | None = None
  fieldBinding: str | None = None
  sequence: int | None = None
  rpcOperation: str | None = None
  rpcContract: str | None = None
  componentGuid: str | None = None


class ServiceObjectsDeleteTreeNodeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str


class ServiceObjectsMoveTreeNodeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  keyGuid: str
  newParentGuid: str | None = None
  newSequence: int = 0


class ServiceObjectsGetComponentTreeParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  componentGuid: str

class ServiceObjectsAnalyzePageParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  pageGuid: str


class ServiceObjectsDeriveQueryParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  pageGuid: str



class ServiceObjectsGetResolvedPropertiesParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  componentGuid: str


class ServiceObjectsUpsertComponentPropertyParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  componentGuid: str
  propertyGuid: str
  value: str | None = None


class ServiceObjectsUpsertTreeNodePropertyParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  treeNodeGuid: str
  propertyGuid: str
  value: str | None = None


class ServiceObjectsDeleteComponentPropertyParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  componentGuid: str
  propertyGuid: str


class ServiceObjectsDeleteTreeNodePropertyParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  treeNodeGuid: str
  propertyGuid: str
