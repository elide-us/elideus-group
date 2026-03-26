"""Identity roles query registry service models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
  "ModifyRoleMemberParams",
  "RoleScopeParams",
  "SetRolesParams",
  "UserGuidParams",
]


def _normalize_uuid(value: Any) -> str:
  return str(value)


class UserGuidParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str

  @field_validator("guid")
  @classmethod
  def _normalize_guid(cls, value: Any) -> str:
    return _normalize_uuid(value)


class SetRolesParams(UserGuidParams):
  roles: int


class RoleScopeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  role: str


class ModifyRoleMemberParams(RoleScopeParams):
  user_guid: str
