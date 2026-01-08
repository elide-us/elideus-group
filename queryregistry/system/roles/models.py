"""System roles query registry service models."""

from __future__ import annotations

from typing import TypedDict

__all__ = [
  "DeleteRolePayload",
  "UpsertRolePayload",
]


class UpsertRolePayload(TypedDict, total=False):
  name: str
  mask: int
  display: str | None


class DeleteRolePayload(TypedDict):
  name: str
