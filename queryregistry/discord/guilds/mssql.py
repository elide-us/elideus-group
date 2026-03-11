"""MSSQL implementations for discord guilds query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "get_guild_v1",
  "list_guilds_v1",
  "update_credits_v1",
  "upsert_guild_v1",
]


async def upsert_guild_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    MERGE discord_guilds AS target
    USING (
      SELECT
        ? AS element_guild_id,
        ? AS element_name,
        ? AS element_joined_on,
        ? AS element_member_count,
        ? AS element_owner_id,
        ? AS element_region,
        ? AS element_left_on,
        ? AS element_notes
    ) AS source
    ON target.element_guild_id = source.element_guild_id
    WHEN MATCHED THEN
      UPDATE SET
        element_name = source.element_name,
        element_member_count = source.element_member_count,
        element_owner_id = source.element_owner_id,
        element_region = source.element_region,
        element_left_on = source.element_left_on,
        element_notes = source.element_notes,
        element_joined_on = COALESCE(source.element_joined_on, target.element_joined_on)
    WHEN NOT MATCHED THEN
      INSERT (
        element_guild_id,
        element_name,
        element_joined_on,
        element_member_count,
        element_owner_id,
        element_region,
        element_left_on,
        element_notes
      ) VALUES (
        source.element_guild_id,
        source.element_name,
        COALESCE(source.element_joined_on, SYSUTCDATETIME()),
        source.element_member_count,
        source.element_owner_id,
        source.element_region,
        source.element_left_on,
        source.element_notes
      )
    OUTPUT
      inserted.recid,
      inserted.element_guild_id,
      inserted.element_name,
      inserted.element_joined_on,
      inserted.element_member_count,
      inserted.element_owner_id,
      inserted.element_region,
      inserted.element_left_on,
      inserted.element_notes,
      inserted.element_credits
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  params = (
    args["guild_id"],
    args["name"],
    args.get("joined_on"),
    args.get("member_count"),
    args.get("owner_id"),
    args.get("region"),
    args.get("left_on"),
    args.get("notes"),
  )
  return await run_json_one(sql, params)


async def get_guild_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guild_id,
      element_name,
      element_joined_on,
      element_member_count,
      element_owner_id,
      element_region,
      element_left_on,
      element_notes,
      element_credits
    FROM discord_guilds
    WHERE element_guild_id = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["guild_id"],))


async def list_guilds_v1(args: Mapping[str, Any]) -> DBResponse:
  include_inactive = args.get("include_inactive", True)
  sql = """
    SELECT
      recid,
      element_guild_id,
      element_name,
      element_joined_on,
      element_member_count,
      element_owner_id,
      element_region,
      element_left_on,
      element_notes,
      element_credits
    FROM discord_guilds
  """
  if not include_inactive:
    sql += "\n    WHERE element_left_on IS NULL"
  sql += "\n    ORDER BY element_joined_on DESC\n    FOR JSON PATH, INCLUDE_NULL_VALUES;"
  return await run_json_many(sql)


async def update_credits_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    UPDATE discord_guilds
    SET element_credits = ?
    WHERE element_guild_id = ?;
  """
  return await run_exec(sql, (args["credits"], args["guild_id"]))
