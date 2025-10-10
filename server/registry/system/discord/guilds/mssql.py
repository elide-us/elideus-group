"""Discord guild queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_json_many, run_json_one
from server.registry.types import DBResponse

__all__ = [
  "get_guild_v1",
  "list_guilds_v1",
  "upsert_guild_v1",
]


async def upsert_guild_v1(args: dict[str, Any]) -> DBResponse:
  guild_id = str(args["guild_id"])
  name = args["name"]
  joined_on = args.get("joined_on")
  member_count = args.get("member_count")
  owner_id = args.get("owner_id")
  if owner_id is not None:
    owner_id = str(owner_id)
  region = args.get("region")
  left_on = args.get("left_on")
  notes = args.get("notes")
  sql = """
    DECLARE @upserted TABLE (
      recid BIGINT,
      element_guild_id NVARCHAR(64),
      element_name NVARCHAR(512),
      element_joined_on DATETIME2(7),
      element_member_count INT,
      element_owner_id NVARCHAR(64),
      element_region NVARCHAR(256),
      element_left_on DATETIME2(7),
      element_notes NVARCHAR(MAX)
    );

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
      inserted.element_notes
    INTO @upserted;

    SELECT
      recid,
      element_guild_id,
      element_name,
      element_joined_on,
      element_member_count,
      element_owner_id,
      element_region,
      element_left_on,
      element_notes
    FROM @upserted
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  params = (
    guild_id,
    name,
    joined_on,
    member_count,
    owner_id,
    region,
    left_on,
    notes,
  )
  return await run_json_one(sql, params)


async def get_guild_v1(args: dict[str, Any]) -> DBResponse:
  guild_id = str(args["guild_id"])
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
      element_notes
    FROM discord_guilds
    WHERE element_guild_id = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (guild_id,))


async def list_guilds_v1(args: dict[str, Any]) -> DBResponse:
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
      element_notes
    FROM discord_guilds
  """
  params: list[Any] = []
  if not include_inactive:
    sql += "\n    WHERE element_left_on IS NULL"
  sql += "\n    ORDER BY element_joined_on DESC\n    FOR JSON PATH, INCLUDE_NULL_VALUES;"
  return await run_json_many(sql, tuple(params))
