"""Finance pipeline config query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeletePipelineConfigParams",
  "GetPipelineConfigParams",
  "ListPipelineConfigsParams",
  "UpsertPipelineConfigParams",
]


class ListPipelineConfigsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  element_pipeline: str | None = None


class GetPipelineConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  element_pipeline: str
  element_key: str


class UpsertPipelineConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  element_pipeline: str
  element_key: str
  element_value: str
  element_description: str | None = None
  element_status: int = 1


class DeletePipelineConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
