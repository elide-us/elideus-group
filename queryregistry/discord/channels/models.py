"""Discord channels query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "BumpChannelActivityParams",
  "ChannelIdParams",
  "ChannelRecord",
  "ListChannelsByGuildParams",
  "UpsertChannelParams",
]


class UpsertChannelParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guilds_recid: int
  channel_id: str
  name: str | None = None
  channel_type: str | None = None
  notes: str | None = None


class ChannelIdParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  channel_id: str


class ListChannelsByGuildParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guilds_recid: int


class BumpChannelActivityParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  channel_id: str


class ChannelRecord(TypedDict):
  recid: int
  guilds_recid: int
  element_channel_id: str
  element_name: str | None
  element_type: str | None
  element_message_count: int
  element_last_activity_on: str | None
  element_created_on: str
  element_modified_on: str
  element_notes: str | None
