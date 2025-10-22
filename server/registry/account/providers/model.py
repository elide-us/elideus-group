"""Typed payload and response models for account provider registry ops."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
  "CreateFromProviderParams",
  "GetUserByEmailParams",
  "LinkProviderParams",
  "ProviderAccountRecord",
  "ProviderIdentifierRecord",
  "ProviderIdentifierParams",
  "ProviderUnlinkSummary",
  "SetProviderParams",
  "SoftDeleteAccountParams",
  "UnlinkLastProviderParams",
  "UnlinkProviderParams",
]


def _normalize_uuid(value: Any) -> str:
  return str(value)


class ProviderIdentifierParams(BaseModel):
  """Payload identifying an account linkage by provider identifier."""

  model_config = ConfigDict(extra="forbid")

  provider: str
  provider_identifier: str

  @field_validator("provider_identifier")
  @classmethod
  def _normalize_identifier(cls, value: Any) -> str:
    return _normalize_uuid(value)


class CreateFromProviderParams(ProviderIdentifierParams):
  """Parameters required to create a user from a provider profile."""

  provider_email: str
  provider_displayname: str
  provider_profile_image: str | None = None


class GetUserByEmailParams(BaseModel):
  """Lookup payload targeting a user by e-mail."""

  model_config = ConfigDict(extra="forbid")

  email: str


class _GuidParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str

  @field_validator("guid")
  @classmethod
  def _normalize_guid(cls, value: Any) -> str:
    return _normalize_uuid(value)


class LinkProviderParams(_GuidParams):
  """Associate an existing account with a provider identifier."""

  provider: str
  provider_identifier: str

  @field_validator("provider_identifier")
  @classmethod
  def _normalize_identifier(cls, value: Any) -> str:
    return _normalize_uuid(value)


class SetProviderParams(_GuidParams):
  """Parameters for setting an account's default provider."""

  provider: str


class SoftDeleteAccountParams(_GuidParams):
  """Parameters for soft-deleting an account."""


class UnlinkProviderParams(_GuidParams):
  """Parameters for unlinking a provider from an account."""

  provider: str
  new_provider_recid: int | None = None


class UnlinkLastProviderParams(_GuidParams):
  """Parameters for unlinking the final provider from an account."""

  provider: str


class ProviderAccountRecord(TypedDict, total=False):
  """Projection returned when hydrating a provider-backed account."""

  guid: str
  display_name: str
  email: str | None
  credits: int | None
  provider_name: str | None
  provider_display: str | None
  profile_image: str | None


class ProviderIdentifierRecord(TypedDict, total=False):
  """Minimal record returned by identifier lookups."""

  guid: str
  element_soft_deleted_at: str | None


class ProviderUnlinkSummary(TypedDict):
  """Summary payload returned after unlinking a provider."""

  providers_remaining: NotRequired[int]
