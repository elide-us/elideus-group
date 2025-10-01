"""Assistant conversation helpers for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation, json_one

__all__ = [
  "find_recent_v1",
  "insert_conversation_v1",
  "list_by_time_v1",
  "list_recent_v1",
  "update_output_v1",
]


def insert_conversation_v1(args: dict[str, Any]) -> Operation:
  personas_recid = args["personas_recid"]
  models_recid = args["models_recid"]
  guild_id = args.get("guild_id")
  channel_id = args.get("channel_id")
  user_id = args.get("user_id")
  input_data = args.get("input_data")
  output_data = args.get("output_data")
  tokens = args.get("tokens")
  sql = """
    INSERT INTO assistant_conversations (
      personas_recid,
      models_recid,
      element_guild_id,
      element_channel_id,
      element_user_id,
      element_input,
      element_output,
      element_tokens
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    SELECT SCOPE_IDENTITY() AS recid
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(
    DbRunMode.JSON_ONE,
    sql,
    (
      personas_recid,
      models_recid,
      guild_id,
      channel_id,
      user_id,
      input_data,
      output_data,
      tokens,
    ),
  )


def find_recent_v1(args: dict[str, Any]):
  personas_recid = args["personas_recid"]
  models_recid = args["models_recid"]
  guild_id = args.get("guild_id")
  channel_id = args.get("channel_id")
  user_id = args.get("user_id")
  input_data = args["input_data"]
  window_seconds = args.get("window_seconds", 300)

  def _norm(value):
    return str(value) if value is not None else None

  guild_id = _norm(guild_id)
  channel_id = _norm(channel_id)
  user_id = _norm(user_id)

  sql = """
    SELECT TOP 1 recid
    FROM assistant_conversations
    WHERE personas_recid = ?
      AND models_recid = ?
      AND element_input = ?
      AND ((element_guild_id = ?) OR (element_guild_id IS NULL AND ? IS NULL))
      AND ((element_channel_id = ?) OR (element_channel_id IS NULL AND ? IS NULL))
      AND ((element_user_id = ?) OR (element_user_id IS NULL AND ? IS NULL))
      AND element_created_on >= DATEADD(second, -?, SYSDATETIMEOFFSET())
    ORDER BY element_created_on DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return json_one(
    sql,
    (
      personas_recid,
      models_recid,
      input_data,
      guild_id,
      guild_id,
      channel_id,
      channel_id,
      user_id,
      user_id,
      window_seconds,
    ),
  )


def update_output_v1(args: dict[str, Any]) -> Operation:
  recid = args["recid"]
  output_data = args.get("output_data")
  tokens = args.get("tokens")
  sql = """
    UPDATE assistant_conversations
    SET element_output = ?,
        element_tokens = ?
    WHERE recid = ?;
  """
  return Operation(DbRunMode.EXEC, sql, (output_data, tokens, recid))


def list_by_time_v1(args: dict[str, Any]) -> Operation:
  personas_recid = args["personas_recid"]
  start = args["start"]
  end = args["end"]
  sql = """
    SELECT recid,
           element_guild_id,
           element_channel_id,
           element_user_id,
           element_input,
           element_output,
           element_tokens,
           element_created_on,
           element_modified_on,
           models_recid
    FROM assistant_conversations
    WHERE personas_recid = ? AND element_created_on BETWEEN ? AND ?
    ORDER BY element_created_on
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return Operation(DbRunMode.JSON_MANY, sql, (personas_recid, start, end))


def list_recent_v1(_: dict[str, Any]) -> Operation:
  sql = """
    SELECT TOP (2)
           recid,
           personas_recid,
           element_guild_id,
           element_channel_id,
           element_user_id,
           element_output,
           element_tokens,
           element_created_on
    FROM assistant_conversations
    WHERE element_output IS NOT NULL AND LTRIM(RTRIM(element_output)) <> ''
    ORDER BY element_created_on DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return Operation(DbRunMode.JSON_MANY, sql, ())
