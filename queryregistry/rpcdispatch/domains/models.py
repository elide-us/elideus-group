"""RPC dispatch domains query registry service models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

class ListDomainsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

class GetDomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class DeleteDomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class UpsertDomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int | None = None
  element_name: str
  element_required_role: str | None = None
  element_is_auth_exempt: bool = False
  element_is_public: bool = False
  element_is_discord: bool = False
  element_status: int = 1
  element_app_version: str | None = None

class GetByNameParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  element_name: str
