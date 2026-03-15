"""System roles query registry service models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeleteRoleParams",
  "UpsertRoleParams",
]


class UpsertRoleParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str
  mask: int
  display: str | None = None


class DeleteRoleParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str
