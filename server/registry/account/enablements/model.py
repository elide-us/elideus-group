"""Typed contracts for user enablement registry operations."""

from __future__ import annotations

from typing import TypedDict

__all__ = [
  "UpsertUserEnablementsParams",
  "UserEnablementsRecord",
]


class UserEnablementsRecord(TypedDict, total=False):
  users_guid: str
  element_enablements: str
  created_on: str
  modified_on: str


class UpsertUserEnablementsParams(TypedDict):
  users_guid: str
  element_enablements: str
