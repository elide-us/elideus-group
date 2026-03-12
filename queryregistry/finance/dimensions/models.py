"""Finance dimensions query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeleteDimensionParams",
  "DimensionRecord",
  "GetDimensionParams",
  "ListDimensionsByNameParams",
  "ListDimensionsParams",
  "UpsertDimensionParams",
]


class ListDimensionsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class ListDimensionsByNameParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str


class GetDimensionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class UpsertDimensionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  name: str
  value: str
  description: str | None = None
  status: int = 1


class DeleteDimensionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class DimensionRecord(TypedDict):
  recid: int
  element_name: str
  element_value: str
  element_description: str | None
  element_status: int
  element_created_on: str
  element_modified_on: str
