"""Typed contracts for user action log registry operations."""

from __future__ import annotations

from typing import NotRequired, TypedDict

__all__ = [
  "ListUserActionsParams",
  "LogUserActionParams",
  "UpdateUserActionParams",
  "UserActionLogRecord",
]


class UserActionLogRecord(TypedDict, total=False):
  recid: int
  users_guid: str
  action_recid: int
  action_label: str | None
  action_description: str | None
  element_url: str | None
  element_logged_on: str
  element_notes: str | None


class ListUserActionsParams(TypedDict):
  users_guid: str
  action_recid: NotRequired[int | None]
  limit: NotRequired[int | None]


class LogUserActionParams(TypedDict):
  recid: int
  users_guid: str
  action_recid: int
  element_url: NotRequired[str | None]
  element_notes: NotRequired[str | None]


class UpdateUserActionParams(TypedDict):
  recid: int
  element_url: NotRequired[str | None]
  element_notes: NotRequired[str | None]
