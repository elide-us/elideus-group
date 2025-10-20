"""Typed contract helpers for assistant conversation registry."""

from __future__ import annotations

from typing import NotRequired, TypedDict

__all__ = [
  "ConversationRecord",
  "FindRecentConversationParams",
  "InsertConversationParams",
  "ListByTimeParams",
  "UpdateConversationOutputParams",
]


class ConversationRecord(TypedDict, total=False):
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
  element_modified_on: str


class InsertConversationParams(TypedDict):
  personas_recid: int
  models_recid: int
  input_data: str
  guild_id: NotRequired[str | int | None]
  channel_id: NotRequired[str | int | None]
  user_id: NotRequired[str | int | None]
  output_data: NotRequired[str | None]
  tokens: NotRequired[int | None]


class FindRecentConversationParams(TypedDict):
  personas_recid: int
  models_recid: int
  input_data: str
  guild_id: NotRequired[str | int | None]
  channel_id: NotRequired[str | int | None]
  user_id: NotRequired[str | int | None]
  window_seconds: NotRequired[int]


class UpdateConversationOutputParams(TypedDict):
  recid: int
  output_data: str | None
  tokens: NotRequired[int | None]


class ListByTimeParams(TypedDict):
  personas_recid: int
  start: str
  end: str
