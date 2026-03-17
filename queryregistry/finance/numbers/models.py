"""Finance numbers query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeleteNumberParams",
  "GetByPrefixAndAccountNumberParams",
  "GetNumberParams",
  "ListNumbersParams",
  "NextNumberParams",
  "NumberRecord",
  "UpsertNumberParams",
]


class ListNumbersParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class GetNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class GetByPrefixAndAccountNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  prefix: str
  account_number: str


class UpsertNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  accounts_guid: str
  prefix: str | None = None
  account_number: str
  last_number: int = 0
  max_number: int | None = None
  allocation_size: int = 1
  reset_policy: str = "Never"
  sequence_status: int = 1
  pattern: str | None = None
  display_format: str | None = None


class DeleteNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class NextNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class NumberRecord(TypedDict):
  recid: int
  accounts_guid: str
  element_prefix: str | None
  element_account_number: str
  element_last_number: int
  element_max_number: int
  element_allocation_size: int
  element_reset_policy: str
  element_sequence_status: int
  element_pattern: str | None
  element_display_format: str | None
  element_created_on: str
  element_modified_on: str
  account_name: str | None
  remaining: int
