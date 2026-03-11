"""Discord channels query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  BumpChannelActivityParams,
  ChannelIdParams,
  ListChannelsByGuildParams,
  UpsertChannelParams,
)

__all__ = [
  "bump_activity_request",
  "get_channel_request",
  "list_by_guild_request",
  "upsert_channel_request",
]


def upsert_channel_request(params: UpsertChannelParams) -> DBRequest:
  return DBRequest(op="db:discord:channels:upsert:1", payload=params.model_dump())


def get_channel_request(params: ChannelIdParams) -> DBRequest:
  return DBRequest(op="db:discord:channels:get:1", payload=params.model_dump())


def list_by_guild_request(params: ListChannelsByGuildParams) -> DBRequest:
  return DBRequest(op="db:discord:channels:list_by_guild:1", payload=params.model_dump())


def bump_activity_request(params: BumpChannelActivityParams) -> DBRequest:
  return DBRequest(op="db:discord:channels:bump_activity:1", payload=params.model_dump())
