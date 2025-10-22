"""Typed payload and response helpers for system role registry operations."""

from __future__ import annotations

from typing import Any, TypedDict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
  "DeleteRoleParams",
  "ModifyRoleMemberParams",
  "RoleMemberRecord",
  "RoleRecord",
  "RoleScopeParams",
  "UpsertRoleParams",
]


def _normalize_uuid(value: Any) -> str:
  return str(UUID(str(value)))


class RoleScopeParams(BaseModel):
  """Payload that scopes operations to a single role."""

  model_config = ConfigDict(extra="forbid")

  role: str


class ModifyRoleMemberParams(RoleScopeParams):
  """Parameters describing a role membership change."""

  user_guid: str

  @field_validator("user_guid")
  @classmethod
  def _normalize_guid(cls, value: Any) -> str:
    return _normalize_uuid(value)


class UpsertRoleParams(BaseModel):
  """Parameters for inserting or updating a role definition."""

  model_config = ConfigDict(extra="forbid")

  name: str
  mask: int
  display: str | None = None


class DeleteRoleParams(BaseModel):
  """Payload describing a role deletion."""

  model_config = ConfigDict(extra="forbid")

  name: str


class RoleRecord(TypedDict, total=False):
  """Role metadata returned when listing roles."""

  name: str
  mask: int
  display: str | None


class RoleMemberRecord(TypedDict, total=False):
  """Projection of a role membership row."""

  guid: str
  display_name: str | None
