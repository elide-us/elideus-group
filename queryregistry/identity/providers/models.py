"""Identity providers query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypedDict

from queryregistry.models import DBResponse

__all__ = [
  "CreateFromProviderCallable",
  "CreateFromProviderRequestPayload",
  "GetAnyByProviderIdentifierCallable",
  "GetAnyByProviderIdentifierPayload",
  "GetAnyByProviderIdentifierRequestPayload",
  "GetByProviderIdentifierCallable",
  "GetByProviderIdentifierPayload",
  "GetByProviderIdentifierRequestPayload",
  "GetUserByEmailCallable",
  "GetUserByEmailPayload",
  "GetUserByEmailRequestPayload",
  "LinkProviderCallable",
  "LinkProviderRequestPayload",
  "RelinkProviderCallable",
  "RelinkProviderRequestPayload",
  "SetProviderCallable",
  "SetProviderRequestPayload",
  "UnlinkLastProviderCallable",
  "UnlinkLastProviderRequestPayload",
  "UnlinkProviderCallable",
  "UnlinkProviderPayload",
  "UnlinkProviderRequestPayload",
]


class GetByProviderIdentifierRequestPayload(TypedDict):
  provider: str
  provider_identifier: str


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
  provider_email: str
  provider_displayname: str
  provider_profile_image: str


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


CreateFromProviderCallable = Callable[[CreateFromProviderRequestPayload], Awaitable[DBResponse]]
GetAnyByProviderIdentifierCallable = Callable[[GetAnyByProviderIdentifierRequestPayload], Awaitable[DBResponse]]
GetByProviderIdentifierCallable = Callable[[GetByProviderIdentifierRequestPayload], Awaitable[DBResponse]]
GetUserByEmailCallable = Callable[[GetUserByEmailRequestPayload], Awaitable[DBResponse]]
LinkProviderCallable = Callable[[LinkProviderRequestPayload], Awaitable[DBResponse]]
UnlinkProviderCallable = Callable[[UnlinkProviderRequestPayload], Awaitable[DBResponse]]
UnlinkLastProviderCallable = Callable[[UnlinkLastProviderRequestPayload], Awaitable[DBResponse]]
SetProviderCallable = Callable[[SetProviderRequestPayload], Awaitable[DBResponse]]
RelinkProviderCallable = Callable[[RelinkProviderRequestPayload], Awaitable[DBResponse]]
