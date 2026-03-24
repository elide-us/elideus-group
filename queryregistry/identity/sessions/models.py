"""Identity sessions query registry service models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, field_validator


__all__ = [
  "CreateSessionParams",
  "GuidParams",
  "ListSessionSnapshotsParams",
  "RotkeyLookupParams",
  "RotkeyRecord",
  "RevokeAllDeviceTokensParams",
  "RevokeDeviceTokenParams",
  "RevokeProviderTokensParams",
  "SessionCreationResult",
  "SessionSnapshotRecord",
  "SecuritySnapshotRecord",
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
  rotkey: str
  rotkey_iat: datetime
  rotkey_exp: datetime
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


class RevokeAllDeviceTokensParams(GuidParams):
  """Payload revoking all device tokens for a user."""


class ListSessionSnapshotsParams(GuidParams):
  """Parameters used for listing session snapshot rows."""


class RotkeyLookupParams(GuidParams):
  """Lookup payload for a device rotation key."""

  device_guid: str | None = None
  fingerprint: str | None = None

  @field_validator("device_guid")
  @classmethod
  def _normalize_device_guid(cls, value: Any | None) -> str | None:
    if value is None:
      return None
    return _normalize_uuid(value)


class SetRotkeyParams(GuidParams):
  """Rotation key payload for device sessions."""

  rotkey: str
  iat: datetime
  exp: datetime
  device_guid: str | None = None

  @field_validator("device_guid")
  @classmethod
  def _normalize_device_guid(cls, value: Any | None) -> str | None:
    if value is None:
      return None
    return _normalize_uuid(value)


class RotkeyRecord(TypedDict, total=False):
  user_guid: str
  user_rotkey: str
  user_rotkey_iat: str
  user_rotkey_exp: str
  device_rotkey: str | None
  device_rotkey_iat: str | None
  device_rotkey_exp: str | None
  provider_name: str | None
  provider_display: str | None
  session_guid: str | None
  session_created_on: str | None
  session_modified_on: str | None
  device_guid: str | None
  device_token: str | None
  device_token_iat: str | None
  device_token_exp: str | None
  revoked_at: str | None
  device_fingerprint: str | None
  user_agent: str | None
  ip_last_seen: str | None


class SecuritySnapshotRecord(TypedDict, total=False):
  user_guid: str
  element_rotkey: str | None
  element_rotkey_iat: str | None
  element_rotkey_exp: str | None
  element_device_rotkey: str | None
  element_device_rotkey_iat: str | None
  element_device_rotkey_exp: str | None
  session_guid: str | None
  device_guid: str | None
  element_token: str | None
  element_token_iat: str | None
  element_token_exp: str | None
  element_revoked_at: str | None
  element_device_fingerprint: str | None
  element_user_agent: str | None
  element_ip_last_seen: str | None


class SessionCreationResult(TypedDict, total=False):
  """Result payload returned after creating a session."""

  session_guid: str
  device_guid: str


class SessionSnapshotRecord(TypedDict, total=False):
  """Historical session snapshot entry."""

  user_guid: str
  user_roles: int | None
  user_created_on: str | None
  user_modified_on: str | None
  element_rotkey: str | None
  element_rotkey_iat: str | None
  element_rotkey_exp: str | None
  element_device_rotkey: str | None
  element_device_rotkey_iat: str | None
  element_device_rotkey_exp: str | None
  session_guid: str | None
  session_created_on: str | None
  session_modified_on: str | None
  device_guid: str | None
  device_created_on: str | None
  device_modified_on: str | None
  element_token: str | None
  element_token_iat: str | None
  element_token_exp: str | None
  element_revoked_at: str | None
  element_device_fingerprint: str | None
  element_user_agent: str | None
  element_ip_last_seen: str | None


