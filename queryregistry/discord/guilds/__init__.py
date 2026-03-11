"""Discord guilds query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import GuildIdParams, ListGuildsParams, UpdateGuildCreditsParams, UpsertGuildParams

__all__ = [
  "get_guild_request",
  "list_guilds_request",
  "update_credits_request",
  "upsert_guild_request",
]


def upsert_guild_request(params: UpsertGuildParams) -> DBRequest:
  return DBRequest(op="db:discord:guilds:upsert:1", payload=params.model_dump())


def get_guild_request(params: GuildIdParams) -> DBRequest:
  return DBRequest(op="db:discord:guilds:get:1", payload=params.model_dump())


def list_guilds_request(params: ListGuildsParams) -> DBRequest:
  return DBRequest(op="db:discord:guilds:list:1", payload=params.model_dump())


def update_credits_request(params: UpdateGuildCreditsParams) -> DBRequest:
  return DBRequest(op="db:discord:guilds:update_credits:1", payload=params.model_dump())
