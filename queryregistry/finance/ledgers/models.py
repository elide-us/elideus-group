"""Finance ledgers query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CreateLedgerParams",
  "DeleteLedgerParams",
  "GetLedgerByNameParams",
  "GetLedgerParams",
  "JournalReferenceCountParams",
  "LedgerRecord",
  "ListLedgersParams",
  "UpdateLedgerParams",
]


class ListLedgersParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class GetLedgerParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class GetLedgerByNameParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  element_name: str


class CreateLedgerParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  element_name: str
  element_description: str | None = None
  element_fiscal_calendar_year: int | None = None
  element_chart_of_accounts_guid: str | None = None
  element_status: int = 1


class UpdateLedgerParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  element_name: str
  element_description: str | None = None
  element_fiscal_calendar_year: int | None = None
  element_chart_of_accounts_guid: str | None = None
  element_status: int = 1


class DeleteLedgerParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class JournalReferenceCountParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class LedgerRecord(TypedDict):
  recid: int
  element_name: str
  element_description: str | None
  element_fiscal_calendar_year: int | None
  element_chart_of_accounts_guid: str | None
  element_status: int
  element_created_on: str
  element_modified_on: str
