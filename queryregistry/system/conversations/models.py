"""System conversations query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "ConversationStatsParams",
  "ConversationRecord",
  "DeleteByThreadParams",
  "DeleteByTimestampParams",
  "FindRecentParams",
  "InsertConversationParams",
  "InsertMessageParams",
  "ListConversationSummaryParams",
  "ListByTimeParams",
  "ListChannelMessagesParams",
  "ListThreadParams",
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




class InsertMessageParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  personas_recid: int
  models_recid: int
  role: str
  content: str
  guild_id: str | None = None
  channel_id: str | None = None
  user_id: str | None = None
  users_guid: str | None = None
  thread_id: str | None = None
  tokens: int | None = None


class ListThreadParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  thread_id: str


class ListChannelMessagesParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guild_id: str
  channel_id: str
  limit: int = 50


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


class ListConversationSummaryParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  limit: int = 100
  offset: int = 0


class DeleteByThreadParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  thread_id: str


class DeleteByTimestampParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  before: str


class ConversationStatsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


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
