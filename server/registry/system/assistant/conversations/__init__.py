"""Assistant conversation registry helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "find_recent_request",
  "insert_conversation_request",
  "list_by_time_request",
  "list_recent_request",
  "register",
  "update_output_request",
]

_OP_PREFIX = "db:system:assistant.conversations"


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
    params={
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
  params = {
    "personas_recid": personas_recid,
    "models_recid": models_recid,
    "guild_id": _normalize_identifier(guild_id),
    "channel_id": _normalize_identifier(channel_id),
    "user_id": _normalize_identifier(user_id),
    "input_data": input_data,
  }
  if window_seconds is not None:
    params["window_seconds"] = window_seconds
  return DBRequest(op=_op("find_recent"), params=params)


def update_output_request(
  *,
  recid: int,
  output_data: str | None,
  tokens: int | None,
) -> DBRequest:
  return DBRequest(
    op=_op("update_output"),
    params={
      "recid": recid,
      "output_data": output_data,
      "tokens": tokens,
    },
  )


def list_by_time_request(*, personas_recid: int, start: str, end: str) -> DBRequest:
  return DBRequest(
    op=_op("list_by_time"),
    params={
      "personas_recid": personas_recid,
      "start": start,
      "end": end,
    },
  )


def list_recent_request() -> DBRequest:
  return DBRequest(op=_op("list_recent"), params={})


def register(router: "SubdomainRouter") -> None:
  router.add_function("find_recent", version=1)
  router.add_function("insert", version=1, implementation="insert_conversation")
  router.add_function("list_by_time", version=1)
  router.add_function("list_recent", version=1)
  router.add_function("update_output", version=1)
