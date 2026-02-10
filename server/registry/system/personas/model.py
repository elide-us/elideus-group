"""Typed contract helpers for assistant persona registry."""

from __future__ import annotations

from typing import NotRequired, TypedDict

__all__ = [
  "DeletePersonaParams",
  "PersonaRecord",
  "PersonaSummary",
  "UpsertPersonaParams",
]


class PersonaRecord(TypedDict, total=False):
  recid: int
  name: str
  prompt: str
  element_prompt: str
  tokens: int
  element_tokens: int
  models_recid: int | None
  model: str | None
  element_model: str | None
  element_created_on: str
  element_modified_on: str


class PersonaSummary(TypedDict, total=False):
  recid: int
  name: str
  prompt: str
  tokens: int
  models_recid: int | None
  model: str | None


class UpsertPersonaParams(TypedDict):
  name: str
  prompt: str
  tokens: int
  models_recid: int
  recid: NotRequired[int | None]


class DeletePersonaParams(TypedDict, total=False):
  recid: NotRequired[int | None]
  name: NotRequired[str | None]
