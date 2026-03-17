"""Finance staging account map query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeleteAccountMapParams",
  "GetAccountMapParams",
  "ListAccountMapParams",
  "ResolveAccountParams",
  "UpsertAccountMapParams",
]


class ListAccountMapParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class GetAccountMapParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class UpsertAccountMapParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  element_service_pattern: str
  element_meter_pattern: str | None = None
  accounts_guid: str
  element_priority: int = 0
  element_description: str | None = None
  element_status: int = 1


class DeleteAccountMapParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class ResolveAccountParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  service_name: str
  meter_category: str | None = None
