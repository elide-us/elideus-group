"""Identity role_memberships query registry service models."""

from __future__ import annotations

from typing import TypedDict

__all__ = [
  "ModifyRoleMemberPayload",
  "RoleScopePayload",
]


class RoleScopePayload(TypedDict):
  role: str


class ModifyRoleMemberPayload(RoleScopePayload):
  user_guid: str
