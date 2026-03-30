"""RPC dispatch models query registry service models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

class ListModelsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

class GetModelParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class DeleteModelParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class UpsertModelParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int | None = None
  element_name: str
  element_domain: str
  element_subdomain: str
  element_version: int = 1
  element_parent_guid: str | None = None
  element_status: int = 1
  element_app_version: str | None = None

class GetByNameParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  element_name: str
