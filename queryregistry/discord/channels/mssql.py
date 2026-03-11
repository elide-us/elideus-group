"""MSSQL implementations for discord channels query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "bump_activity_v1",
  "get_channel_v1",
  "list_by_guild_v1",
  "upsert_channel_v1",
]


async def upsert_channel_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    MERGE discord_channels AS target
    USING (
      SELECT
        ? AS guilds_recid,
        ? AS element_channel_id,
        ? AS element_name,
        ? AS element_type,
        ? AS element_notes
    ) AS source
    ON target.element_channel_id = source.element_channel_id
    WHEN MATCHED THEN
      UPDATE SET
        guilds_recid = source.guilds_recid,
        element_name = source.element_name,
        element_type = source.element_type,
        element_notes = source.element_notes,
        element_message_count = target.element_message_count + 1,
        element_last_activity_on = SYSUTCDATETIME(),
        element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        guilds_recid,
        element_channel_id,
        element_name,
        element_type,
        element_notes,
        element_message_count,
        element_last_activity_on
      ) VALUES (
        source.guilds_recid,
        source.element_channel_id,
        source.element_name,
        source.element_type,
        source.element_notes,
        1,
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid,
      inserted.guilds_recid,
      inserted.element_channel_id,
      inserted.element_name,
      inserted.element_type,
      inserted.element_message_count,
      inserted.element_last_activity_on,
      inserted.element_created_on,
      inserted.element_modified_on,
      inserted.element_notes
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  params = (
    args["guilds_recid"],
    args["channel_id"],
    args.get("name"),
    args.get("channel_type"),
    args.get("notes"),
  )
  return await run_json_one(sql, params)


async def get_channel_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      guilds_recid,
      element_channel_id,
      element_name,
      element_type,
      element_message_count,
      element_last_activity_on,
      element_created_on,
      element_modified_on,
      element_notes
    FROM discord_channels
    WHERE element_channel_id = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["channel_id"],))


async def list_by_guild_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      guilds_recid,
      element_channel_id,
      element_name,
      element_type,
      element_message_count,
      element_last_activity_on,
      element_created_on,
      element_modified_on,
      element_notes
    FROM discord_channels
    WHERE guilds_recid = ?
    ORDER BY element_last_activity_on DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["guilds_recid"],))


async def bump_activity_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    UPDATE discord_channels
    SET element_message_count = element_message_count + 1,
        element_last_activity_on = SYSUTCDATETIME(),
        element_modified_on = SYSUTCDATETIME()
    WHERE element_channel_id = ?;
  """
  return await run_exec(sql, (args["channel_id"],))
