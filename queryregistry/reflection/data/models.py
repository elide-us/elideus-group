"""Reflection data query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "BatchParams",
  "DumpTableParams",
  "UpdateVersionParams",
  "QueryInfoSchemaParams",
  "VersionParams",
  "VersionRecord",
]


class VersionParams(BaseModel):
  """Payload for fetching current system version."""

  model_config = ConfigDict(extra="forbid")


class UpdateVersionParams(BaseModel):
  """Payload for updating current system version."""

  model_config = ConfigDict(extra="forbid")

  version: str


class DumpTableParams(BaseModel):
  """Payload for exporting table rows as JSON."""

  model_config = ConfigDict(extra="forbid")

  table_schema: str
  name: str


class BatchParams(BaseModel):
  """Payload for executing a SQL batch."""

  model_config = ConfigDict(extra="forbid")

  sql: str


class QueryInfoSchemaParams(BaseModel):
  """Payload for querying INFORMATION_SCHEMA views."""

  model_config = ConfigDict(extra="forbid")

  view_name: str
  filter_column: str | None = None
  filter_value: str | None = None


class VersionRecord(TypedDict):
  """Version record from system_config."""

  element_key: str
  element_value: str
