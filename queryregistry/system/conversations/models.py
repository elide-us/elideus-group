"""System conversations query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "ConversationRecord",
  "FindRecentParams",
  "InsertConversationParams",
  "ListByTimeParams",
  "UpdateOutputParams",
]


class InsertConversationParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  personas_recid: int
  models_recid: int
  input_data: str
  guild_id: str | None = None
  channel_id: str | None = None
  user_id: str | None = None
  output_data: str | None = None
  tokens: int | None = None


class FindRecentParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  personas_recid: int
  models_recid: int
  input_data: str
  guild_id: str | None = None
  channel_id: str | None = None
  user_id: str | None = None
  window_seconds: int = 300


class UpdateOutputParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  output_data: str | None = None
  tokens: int | None = None


class ListByTimeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  personas_recid: int
  start: str
  end: str


class ConversationRecord(TypedDict):
  recid: int
  personas_recid: int
  models_recid: int
  element_guild_id: str | None
  element_channel_id: str | None
  element_user_id: str | None
  element_input: str
  element_output: str | None
  element_tokens: int | None
  element_created_on: str
