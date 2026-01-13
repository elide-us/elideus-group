"""Identity profile query registry service models."""

from __future__ import annotations

from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
  "GuidParams",
  "ProfileRecord",
  "SetDisplayParams",
  "SetOptInParams",
  "SetProfileImageParams",
  "SetRolesParams",
  "UpdateIfUneditedParams",
]


def _normalize_uuid(value: Any) -> str:
  return str(value)


class GuidParams(BaseModel):
  """Base payload carrying a profile guid."""

  model_config = ConfigDict(extra="forbid")

  guid: str

  @field_validator("guid")
  @classmethod
  def _normalize_guid(cls, value: Any) -> str:
    return _normalize_uuid(value)


class SetDisplayParams(GuidParams):
  """Parameters for updating a user's display name."""

  display_name: str


class SetOptInParams(GuidParams):
  """Parameters controlling opt-in email visibility."""

  display_email: bool


class SetProfileImageParams(GuidParams):
  """Payload used to set or clear the user's profile image."""

  provider: str
  image_b64: str | None


class SetRolesParams(GuidParams):
  """Parameters used to update the user's role mask."""

  roles: int


class UpdateIfUneditedParams(GuidParams):
  """Parameters for updating profile fields if untouched by the user."""

  display_name: str | None = None
  email: str | None = None


class ProfileRecord(TypedDict, total=False):
  """Projection returned by profile queries."""

  guid: str
  display_name: str | None
  email: str | None
  credits: int | None
  profile_image: str | None
  default_provider: str | None
  roles: int | None
  element_created_on: str | None
  element_modified_on: str | None
