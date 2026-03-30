"""RPC dispatch functions query registry service models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

class ListFunctionsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

class GetFunctionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int | None = None
  guid: str | None = None

class DeleteFunctionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class UpsertFunctionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int | None = None
  subdomains_guid: str
  element_name: str
  element_version: int = 1
  element_module_attr: str
  element_method_name: str
  element_request_model_guid: str | None = None
  element_response_model_guid: str | None = None
  element_status: int = 1
  element_app_version: str | None = None

class ListBySubdomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  subdomains_guid: str
