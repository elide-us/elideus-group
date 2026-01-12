"""Identity sessions query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

from queryregistry.models import DBResponse

__all__ = [
  "CreateSessionParams",
  "GuidParams",
  "RevokeDeviceTokenParams",
  "RevokeProviderTokensParams",
  "SecuritySnapshotCallable",
  "SecuritySnapshotRecord",
  "SecuritySnapshotRequestPayload",
  "SetRotkeyParams",
  "UpdateDeviceTokenParams",
  "UpdateSessionParams",
]


def _normalize_uuid(value: Any) -> str:
  return str(value)


class GuidParams(BaseModel):
  """Generic payload carrying a user guid."""

  model_config = ConfigDict(extra="forbid")

  guid: str

  @field_validator("guid")
  @classmethod
  def _normalize_guid(cls, value: Any) -> str:
    return _normalize_uuid(value)


class CreateSessionParams(BaseModel):
  """Payload required to create or refresh a device session."""

  model_config = ConfigDict(extra="forbid")

  access_token: str
  expires: datetime
  fingerprint: str
  user_guid: str
  provider: str
  user_agent: str | None = None
  ip_address: str | None = None

  @field_validator("user_guid")
  @classmethod
  def _normalize_user_guid(cls, value: Any) -> str:
    return _normalize_uuid(value)


class UpdateSessionParams(BaseModel):
  """Metadata attached to an existing device session."""

  model_config = ConfigDict(extra="forbid")

  access_token: str
  user_agent: str | None
  ip_address: str | None


class UpdateDeviceTokenParams(BaseModel):
  """Payload targeting a device token by guid."""

  model_config = ConfigDict(extra="forbid")

  device_guid: str
  access_token: str

  @field_validator("device_guid")
  @classmethod
  def _normalize_guid(cls, value: Any) -> str:
    return _normalize_uuid(value)


class RevokeDeviceTokenParams(BaseModel):
  """Payload targeting an access token for revocation."""

  model_config = ConfigDict(extra="forbid")

  access_token: str


class RevokeProviderTokensParams(GuidParams):
  """Payload revoking tokens associated with a provider."""

  provider: str


class SetRotkeyParams(GuidParams):
  """Rotation key payload for a user."""

  rotkey: str
  iat: datetime
  exp: datetime


class SecuritySnapshotRequestPayload(TypedDict):
  guid: str


class SecuritySnapshotRecord(TypedDict, total=False):
  user_guid: str
  element_rotkey: str | None
  element_rotkey_iat: str | None
  element_rotkey_exp: str | None
  session_guid: str | None
  device_guid: str | None
  element_token: str | None
  element_token_iat: str | None
  element_token_exp: str | None
  element_revoked_at: str | None
  element_device_fingerprint: str | None
  element_user_agent: str | None
  element_ip_last_seen: str | None


SecuritySnapshotCallable = Callable[[SecuritySnapshotRequestPayload], Awaitable[DBResponse]]
