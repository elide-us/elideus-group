"""Discord guilds query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "GuildIdParams",
  "GuildRecord",
  "ListGuildsParams",
  "UpdateGuildCreditsParams",
  "UpsertGuildParams",
]


class UpsertGuildParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guild_id: str
  name: str
  joined_on: str | None = None
  member_count: int | None = None
  owner_id: str | None = None
  region: str | None = None
  left_on: str | None = None
  notes: str | None = None


class GuildIdParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guild_id: str


class ListGuildsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  include_inactive: bool = True


class UpdateGuildCreditsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guild_id: str
  credits: int


class GuildRecord(TypedDict):
  recid: int
  element_guild_id: str
  element_name: str
  element_joined_on: str
  element_member_count: int | None
  element_owner_id: str | None
  element_region: str | None
  element_left_on: str | None
  element_notes: str | None
  element_credits: int
