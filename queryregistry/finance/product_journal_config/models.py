"""Finance product journal config query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "ActivateProductJournalConfigParams",
  "ApproveProductJournalConfigParams",
  "CloseProductJournalConfigParams",
  "GetActiveConfigParams",
  "GetProductJournalConfigParams",
  "ListProductJournalConfigParams",
  "UpsertProductJournalConfigParams",
]


class ListProductJournalConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  category: str | None = None
  periods_guid: str | None = None
  status: int | None = None


class GetProductJournalConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class GetActiveConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  category: str
  periods_guid: str


class UpsertProductJournalConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  category: str
  journal_scope: str
  journals_recid: int
  periods_guid: str
  status: int = 0


class ApproveProductJournalConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  approved_by: str


class ActivateProductJournalConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  activated_by: str


class CloseProductJournalConfigParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
