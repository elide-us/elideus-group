"""System config query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "ConfigKeyParams",
  "ConfigRecord",
  "UpsertConfigParams",
]


class ConfigKeyParams(BaseModel):
  """Payload targeting a single configuration entry."""

  model_config = ConfigDict(extra="forbid")

  key: str


class UpsertConfigParams(BaseModel):
  """Parameters for inserting or updating a configuration value."""

  model_config = ConfigDict(extra="forbid")

  key: str
  value: str


class ConfigRecord(TypedDict):
  """Record representation returned by configuration queries."""

  key: str
  value: str
