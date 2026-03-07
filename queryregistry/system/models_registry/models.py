"""System models query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "ModelNameParams",
  "ModelRecord",
]


class ModelNameParams(BaseModel):
  """Payload targeting a single assistant model by name."""

  model_config = ConfigDict(extra="forbid")

  name: str


class ModelRecord(TypedDict):
  """Record representation returned by model queries."""

  recid: int
  name: str
