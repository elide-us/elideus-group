"""Identity providers query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

from queryregistry.models import DBResponse

__all__ = [
  "CreateFromProviderCallable",
  "CreateFromProviderParams",
  "CreateFromProviderRequestPayload",
  "GetAnyByProviderIdentifierCallable",
  "GetAnyByProviderIdentifierParams",
  "GetAnyByProviderIdentifierPayload",
  "GetAnyByProviderIdentifierRequestPayload",
  "GetByProviderIdentifierCallable",
  "GetByProviderIdentifierPayload",
  "GetByProviderIdentifierRequestPayload",
  "GetUserByEmailParams",
  "GetUserByEmailCallable",
  "GetUserByEmailPayload",
  "GetUserByEmailRequestPayload",
  "LinkProviderParams",
  "LinkProviderCallable",
  "LinkProviderRequestPayload",
  "ProviderAccountRecord",
  "ProviderIdentifierParams",
  "ProviderIdentifierRecord",
  "ProviderUnlinkSummary",
  "RelinkProviderCallable",
  "RelinkProviderRequestPayload",
  "SetProviderParams",
  "SetProviderCallable",
  "SetProviderRequestPayload",
  "SoftDeleteAccountCallable",
  "SoftDeleteAccountRequestPayload",
  "UnlinkLastProviderParams",
  "UnlinkLastProviderCallable",
  "UnlinkLastProviderRequestPayload",
  "UnlinkProviderParams",
  "UnlinkProviderCallable",
  "UnlinkProviderPayload",
  "UnlinkProviderRequestPayload",
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


class GetByProviderIdentifierRequestPayload(TypedDict):
  provider: str
  provider_identifier: str




class GetAnyByProviderIdentifierParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  provider_identifier: str

  @field_validator("provider_identifier")
  @classmethod
  def _normalize_identifier(cls, value: Any) -> str:
    return _normalize_uuid(value)


class GetByProviderIdentifierPayload(TypedDict, total=False):
  guid: str
  display_name: str
  email: str
  credits: int
  provider_name: str
  provider_display: str
  profile_image: str


class GetAnyByProviderIdentifierRequestPayload(TypedDict):
  provider_identifier: str


class GetAnyByProviderIdentifierPayload(TypedDict, total=False):
  guid: str
  element_soft_deleted_at: str | None


class GetUserByEmailRequestPayload(TypedDict):
  email: str


class GetUserByEmailPayload(TypedDict, total=False):
  guid: str


class CreateFromProviderRequestPayload(TypedDict, total=False):
  provider: str
  provider_identifier: str
  email: str
  displayname: str
  profile_image: str


class LinkProviderRequestPayload(TypedDict):
  guid: str
  provider: str
  provider_identifier: str


class UnlinkProviderRequestPayload(TypedDict, total=False):
  guid: str
  provider: str
  new_provider_recid: int


class UnlinkProviderPayload(TypedDict):
  providers_remaining: int


class UnlinkLastProviderRequestPayload(TypedDict):
  guid: str
  provider: str


class SetProviderRequestPayload(TypedDict):
  guid: str
  provider: str


class RelinkProviderRequestPayload(TypedDict, total=False):
  provider: str
  provider_identifier: str
  email: str
  display_name: str
  profile_image: str
  confirm: bool
  reauth_token: str


class SoftDeleteAccountRequestPayload(TypedDict):
  guid: str


CreateFromProviderCallable = Callable[[CreateFromProviderRequestPayload], Awaitable[DBResponse]]
GetAnyByProviderIdentifierCallable = Callable[[GetAnyByProviderIdentifierRequestPayload], Awaitable[DBResponse]]
GetByProviderIdentifierCallable = Callable[[GetByProviderIdentifierRequestPayload], Awaitable[DBResponse]]
GetUserByEmailCallable = Callable[[GetUserByEmailRequestPayload], Awaitable[DBResponse]]
LinkProviderCallable = Callable[[LinkProviderRequestPayload], Awaitable[DBResponse]]
UnlinkProviderCallable = Callable[[UnlinkProviderRequestPayload], Awaitable[DBResponse]]
UnlinkLastProviderCallable = Callable[[UnlinkLastProviderRequestPayload], Awaitable[DBResponse]]
SetProviderCallable = Callable[[SetProviderRequestPayload], Awaitable[DBResponse]]
RelinkProviderCallable = Callable[[RelinkProviderRequestPayload], Awaitable[DBResponse]]
SoftDeleteAccountCallable = Callable[[SoftDeleteAccountRequestPayload], Awaitable[DBResponse]]
