"""Identity auth query registry service models."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict, field_validator


__all__ = [
  "CreateFromProviderParams",
  "GetAnyByProviderIdentifierParams",
  "GetUserByEmailParams",
  "LinkProviderParams",
  "ProviderAccountRecord",
  "ProviderIdentifierParams",
  "ProviderIdentifierRecord",
  "ProviderUnlinkSummary",
  "SetProviderParams",
  "UnlinkLastProviderParams",
  "UnlinkProviderParams",
]


def _normalize_uuid(value: Any) -> str:
  return str(value)


class ProviderIdentifierParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  provider: str
  provider_identifier: str

  @field_validator("provider_identifier")
  @classmethod
  def _normalize_identifier(cls, value: Any) -> str:
    return _normalize_uuid(value)


class CreateFromProviderParams(ProviderIdentifierParams):
  email: str
  displayname: str
  profile_image: str | None = None




class GetAnyByProviderIdentifierParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  provider_identifier: str

  @field_validator("provider_identifier")
  @classmethod
  def _normalize_identifier(cls, value: Any) -> str:
    return _normalize_uuid(value)


class GetUserByEmailParams(BaseModel):
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
  provider: str
  provider_identifier: str

  @field_validator("provider_identifier")
  @classmethod
  def _normalize_identifier(cls, value: Any) -> str:
    return _normalize_uuid(value)


class SetProviderParams(_GuidParams):
  provider: str


class UnlinkProviderParams(_GuidParams):
  provider: str
  new_provider_recid: int | None = None


class UnlinkLastProviderParams(_GuidParams):
  provider: str


class ProviderAccountRecord(TypedDict, total=False):
  guid: str
  display_name: str
  email: str | None
  credits: int | None
  provider_name: str | None
  provider_display: str | None
  profile_image: str | None


class ProviderIdentifierRecord(TypedDict, total=False):
  guid: str
  element_soft_deleted_at: str | None


class ProviderUnlinkSummary(TypedDict):
  providers_remaining: NotRequired[int]


