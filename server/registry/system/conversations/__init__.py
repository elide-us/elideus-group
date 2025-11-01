"""Assistant conversation registry helpers."""

from __future__ import annotations

from typing import Any

from server.registry.types import DBRequest

from .model import (
  ConversationRecord,
  FindRecentConversationParams,
  InsertConversationParams,
  ListByTimeParams,
  UpdateConversationOutputParams,
)

__all__ = [
  "find_recent_request",
  "insert_conversation_request",
  "list_by_time_request",
  "list_recent_request",
  "update_output_request",
  "ConversationRecord",
  "FindRecentConversationParams",
  "InsertConversationParams",
  "ListByTimeParams",
  "UpdateConversationOutputParams",
]

_OP_PREFIX = "db:system:conversations"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def _normalize_identifier(value: Any) -> str | None:
  if value is None:
    return None
  return str(value)


def insert_conversation_request(
  *,
  personas_recid: int,
  models_recid: int,
  guild_id: str | int | None,
  channel_id: str | int | None,
  user_id: str | int | None,
  input_data: str,
  output_data: str | None = None,
  tokens: int | None = None,
) -> DBRequest:
  return DBRequest(
    op=_op("insert"),
    payload={
      "personas_recid": personas_recid,
      "models_recid": models_recid,
      "guild_id": _normalize_identifier(guild_id),
      "channel_id": _normalize_identifier(channel_id),
      "user_id": _normalize_identifier(user_id),
      "input_data": input_data,
      "output_data": output_data,
      "tokens": tokens,
    },
  )


def find_recent_request(
  *,
  personas_recid: int,
  models_recid: int,
  guild_id: str | int | None,
  channel_id: str | int | None,
  user_id: str | int | None,
  input_data: str,
  window_seconds: int | None = None,
) -> DBRequest:
  payload = {
    "personas_recid": personas_recid,
    "models_recid": models_recid,
    "guild_id": _normalize_identifier(guild_id),
    "channel_id": _normalize_identifier(channel_id),
    "user_id": _normalize_identifier(user_id),
    "input_data": input_data,
  }
  if window_seconds is not None:
    payload["window_seconds"] = window_seconds
  return DBRequest(op=_op("find_recent"), payload=payload)


def update_output_request(
  *,
  recid: int,
  output_data: str | None,
  tokens: int | None,
) -> DBRequest:
  return DBRequest(
    op=_op("update_output"),
    payload={
      "recid": recid,
      "output_data": output_data,
      "tokens": tokens,
    },
  )


def list_by_time_request(*, personas_recid: int, start: str, end: str) -> DBRequest:
  return DBRequest(
    op=_op("list_by_time"),
    payload={
      "personas_recid": personas_recid,
      "start": start,
      "end": end,
    },
  )


def list_recent_request() -> DBRequest:
  return DBRequest(op=_op("list_recent"), payload={})
