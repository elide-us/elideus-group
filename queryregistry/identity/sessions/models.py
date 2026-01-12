"""Identity sessions query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

from queryregistry.models import DBResponse

__all__ = [
  "GuidParams",
  "SecuritySnapshotCallable",
  "SecuritySnapshotRecord",
  "SecuritySnapshotRequestPayload",
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
