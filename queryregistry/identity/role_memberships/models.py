"""Identity role_memberships query registry service models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "ModifyRoleMemberParams",
  "RoleScopeParams",
]


class RoleScopeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  role: str


class ModifyRoleMemberParams(RoleScopeParams):
  user_guid: str
