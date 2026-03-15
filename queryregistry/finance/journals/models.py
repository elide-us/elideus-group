"""Finance journals query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CreateJournalParams",
  "GetByPostingKeyParams",
  "GetJournalParams",
  "JournalRecord",
  "ListJournalsParams",
  "UpdateJournalStatusParams",
]


class ListJournalsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  status: int | None = None
  periods_guid: str | None = None


class GetJournalParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class CreateJournalParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str
  description: str | None = None
  posting_key: str | None = None
  source_type: str | None = None
  source_id: str | None = None
  periods_guid: str | None = None
  ledgers_recid: int | None = None
  numbers_recid: int | None = None
  status: int = 0


class UpdateJournalStatusParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  status: int
  posted_by: str | None = None
  posted_on: str | None = None
  reversed_by: int | None = None
  reversal_of: int | None = None


class GetByPostingKeyParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  posting_key: str


class JournalRecord(TypedDict):
  recid: int
  element_name: str
  element_description: str | None
  numbers_recid: int | None
  element_status: int
  element_created_on: str
  element_modified_on: str
  element_posting_key: str | None
  element_source_type: str | None
  element_source_id: str | None
  periods_guid: str | None
  ledgers_recid: int | None
  element_posted_by: str | None
  element_posted_on: str | None
  element_reversed_by: int | None
  element_reversal_of: int | None
