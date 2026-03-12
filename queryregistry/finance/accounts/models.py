"""Finance accounts query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "AccountRecord",
  "DeleteAccountParams",
  "GetAccountParams",
  "ListAccountsParams",
  "ListChildrenParams",
  "UpsertAccountParams",
]


class ListAccountsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class GetAccountParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class UpsertAccountParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str | None = None
  number: str
  name: str
  account_type: int
  parent: str | None = None
  is_posting: bool = True
  status: int = 1


class DeleteAccountParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class ListChildrenParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  parent_guid: str


class AccountRecord(TypedDict):
  element_guid: str
  element_number: str
  element_name: str
  element_type: int
  element_parent: str | None
  is_posting: bool
  element_status: int
  element_created_on: str
  element_modified_on: str
