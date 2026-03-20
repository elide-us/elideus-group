"""Finance staging query registry models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
  "AggregateCostByServiceParams",
  "ApproveImportParams",
  "CreateImportParams",
  "DeleteImportParams",
  "InsertCostDetailBatchParams",
  "ListCostDetailsByImportParams",
  "ListImportsParams",
  "RejectImportParams",
  "UpdateImportStatusParams",
]


class AggregateCostByServiceParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int


class ApproveImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
  approved_by: str


class CreateImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  source: str
  scope: str
  metric: str
  period_start: str
  period_end: str
  requested_by: str | None = None
  initial_status: int = 0


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


class DeleteImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int


class ListImportsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  status: int | None = None


class ListCostDetailsByImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int


class RejectImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
  approved_by: str
  reason: str | None = None
