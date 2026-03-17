from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ListVendorsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class GetVendorParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class GetVendorByNameParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  element_name: str


class UpsertVendorParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  element_name: str
  element_display: str | None = None
  element_description: str | None = None
  element_status: int = 1


class DeleteVendorParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
