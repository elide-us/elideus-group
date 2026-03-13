"""Identity accounts query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from queryregistry.models import DBResponse

__all__ = [
  "AccountExistsCallable",
  "AccountExistsPayload",
  "AccountExistsRequestPayload",
  "AccountsReadCallable",
  "DiscordSecurityCallable",
  "DiscordSecurityPayload",
  "DiscordSecurityRequestPayload",
  "SecurityProfilePayload",
  "SecurityProfileRequestPayload",
]


class SecurityProfileRequestPayload(TypedDict, total=False):
  guid: str
  access_token: str
  provider: str
  provider_identifier: str
  discord_id: str


class SecurityProfilePayload(TypedDict, total=False):
  user_guid: str
  guid: str
  user_roles: int
  element_roles: int
  user_created_on: str
  user_modified_on: str
  element_rotkey: str
  rotkey: str
  element_rotkey_iat: str
  element_rotkey_exp: str
  provider_name: str
  provider_display: str
  providers_recid: int
  session_guid: str
  session_created_on: str
  session_created_at: str
  session_modified_on: str
  device_guid: str
  device_created_on: str
  device_modified_on: str
  element_token: str
  token: str
  element_token_iat: str
  issued_at: str
  element_token_exp: str
  expires_at: str
  element_revoked_at: str
  revoked_at: str
  element_device_fingerprint: str
  device_fingerprint: str
  element_user_agent: str
  user_agent: str
  element_ip_last_seen: str
  ip_last_seen: str
  extra: dict[str, Any]




class DiscordSecurityRequestPayload(TypedDict):
  discord_id: str


class DiscordSecurityPayload(TypedDict, total=False):
  user_guid: str
  user_roles: int


class AccountExistsRequestPayload(TypedDict):
  user_guid: str


class AccountExistsPayload(TypedDict):
  exists_flag: int


AccountsReadCallable = Callable[[SecurityProfileRequestPayload], Awaitable[DBResponse]]
AccountExistsCallable = Callable[[AccountExistsRequestPayload], Awaitable[DBResponse]]
DiscordSecurityCallable = Callable[[DiscordSecurityRequestPayload], Awaitable[DBResponse]]
