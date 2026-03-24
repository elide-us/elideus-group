"""RPC dispatch subdomains query registry service models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

class ListSubdomainsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

class GetSubdomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class DeleteSubdomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class UpsertSubdomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int | None = None
  domains_recid: int
  element_name: str
  element_entitlement_mask: int = 0
  element_status: int = 1
  element_app_version: str | None = None

class ListByDomainParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  domains_recid: int
