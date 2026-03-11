"""System personas query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeletePersonaParams",
  "PersonaNameParams",
  "PersonaRecord",
  "UpsertPersonaParams",
]


class PersonaNameParams(BaseModel):
  """Payload targeting a single persona by name."""

  model_config = ConfigDict(extra="forbid")

  name: str


class UpsertPersonaParams(BaseModel):
  """Parameters for inserting or updating a persona."""

  model_config = ConfigDict(extra="forbid")

  name: str
  prompt: str
  tokens: int
  models_recid: int
  is_active: bool = True
  recid: int | None = None


class DeletePersonaParams(BaseModel):
  """Parameters for deleting a persona by recid or name."""

  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  name: str | None = None


class PersonaRecord(TypedDict):
  """Record representation returned by persona queries."""

  recid: int
  name: str
  prompt: str
  tokens: int
  models_recid: int | None
  model: str | None
  element_created_on: str
  element_modified_on: str
