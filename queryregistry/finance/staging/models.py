"""Finance staging query registry models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CreateImportParams",
  "InsertCostDetailBatchParams",
  "ListCostDetailsByImportParams",
  "ListImportsParams",
  "UpdateImportStatusParams",
]


class CreateImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  source: str
  scope: str
  metric: str
  period_start: str
  period_end: str


class UpdateImportStatusParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int
  row_count: int
  error: str | None = None


class InsertCostDetailBatchParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
  rows: list[dict[str, Any]]


class ListImportsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class ListCostDetailsByImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
