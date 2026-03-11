"""System models query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeleteModelParams",
  "ModelNameParams",
  "ModelRecord",
  "UpsertModelParams",
]


class ModelNameParams(BaseModel):
  """Payload targeting a single assistant model by name."""

  model_config = ConfigDict(extra="forbid")

  name: str


class UpsertModelParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  name: str
  api_provider: str = "openai"
  is_active: bool = True


class DeleteModelParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  name: str | None = None


class ModelRecord(TypedDict):
  """Record representation returned by model queries."""

  recid: int
  name: str
  api_provider: str
  is_active: bool
