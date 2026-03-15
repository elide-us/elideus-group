"""Finance journal lines query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
  "CreateLineParams",
  "CreateLinesBatchParams",
  "DeleteLinesByJournalParams",
  "JournalLineDimensionRecord",
  "JournalLineRecord",
  "ListLinesByJournalParams",
]


class ListLinesByJournalParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  journals_recid: int


class CreateLineParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  journals_recid: int
  line_number: int
  accounts_guid: str
  debit: str = "0"
  credit: str = "0"
  description: str | None = None
  dimension_recids: list[int] = Field(default_factory=list)


class CreateLinesBatchParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  journals_recid: int
  lines: list[CreateLineParams]


class DeleteLinesByJournalParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  journals_recid: int


class JournalLineRecord(TypedDict):
  recid: int
  journals_recid: int
  element_line_number: int
  accounts_guid: str
  element_debit: str
  element_credit: str
  element_description: str | None
  element_created_on: str
  element_modified_on: str
  dimension_recids: list[int]


class JournalLineDimensionRecord(TypedDict):
  recid: int
  lines_recid: int
  dimensions_recid: int
