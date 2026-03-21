"""Finance numbers query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CloseSequenceParams",
  "DeleteNumberParams",
  "GetByScopeParams",
  "GetByPrefixAndAccountNumberParams",
  "GetNumberParams",
  "ListNumbersParams",
  "NextNumberByScopeParams",
  "NextNumberParams",
  "NumberRecord",
  "ShiftNumberParams",
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


class GetByScopeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  prefix: str
  scope: str


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
  sequence_type: str = "continuous"
  series_number: int = 1
  scope: str | None = None
  pattern: str | None = None
  display_format: str | None = None


class DeleteNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class CloseSequenceParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class NextNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class NextNumberByScopeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  prefix: str
  scope: str


class ShiftNumberParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  current_recid: int
  new_prefix: str | None = None
  new_account_number: str
  new_display_format: str | None = None
  new_pattern: str | None = None
  new_allocation_size: int = 1


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
  element_sequence_type: str
  element_series_number: int
  element_scope: str | None
  element_pattern: str | None
  element_display_format: str | None
  element_created_on: str
  element_modified_on: str
  account_name: str | None
  remaining: int
