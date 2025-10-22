"""Typed payload and response helpers for system config registry ops."""

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


class UpsertConfigParams(ConfigKeyParams):
  """Parameters for inserting or updating a configuration value."""

  value: str


class ConfigRecord(TypedDict, total=False):
  """Record representation returned by configuration queries."""

  key: str
  value: str | None
