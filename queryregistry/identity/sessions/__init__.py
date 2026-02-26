"""Identity sessions query registry helpers."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateSessionParams,
  GuidParams,
  ListSessionSnapshotsParams,
  RevokeAllDeviceTokensParams,
  RevokeDeviceTokenParams,
  RevokeProviderTokensParams,
  RotkeyLookupParams,
  SetRotkeyParams,
  UpdateDeviceTokenParams,
  UpdateSessionParams,
)

__all__ = [
  "create_session_request",
  "get_rotkey_request",
  "list_snapshots_request",
  "read_sessions_request",
  "revoke_all_device_tokens_request",
  "revoke_device_token_request",
  "revoke_provider_tokens_request",
  "set_rotkey_request",
  "update_device_token_request",
  "update_session_request",
]


def _request(name: str, payload: dict[str, object]) -> DBRequest:
  return DBRequest(op=f"db:identity:sessions:{name}:1", payload=payload)


def get_rotkey_request(params: RotkeyLookupParams) -> DBRequest:
  return _request("get_rotkey", params.model_dump(exclude_none=True))


def read_sessions_request(params: GuidParams) -> DBRequest:
  return _request("read", params.model_dump())


def create_session_request(params: CreateSessionParams) -> DBRequest:
  return _request("create_session", params.model_dump(exclude_none=True))


def update_session_request(params: UpdateSessionParams) -> DBRequest:
  return _request("update_session", params.model_dump())


def update_device_token_request(params: UpdateDeviceTokenParams) -> DBRequest:
  return _request("update_device_token", params.model_dump())


def revoke_device_token_request(params: RevokeDeviceTokenParams) -> DBRequest:
  return _request("revoke_device_token", params.model_dump())


def revoke_all_device_tokens_request(params: RevokeAllDeviceTokensParams) -> DBRequest:
  return _request("revoke_all_device_tokens", params.model_dump())


def revoke_provider_tokens_request(params: RevokeProviderTokensParams) -> DBRequest:
  return _request("revoke_provider_tokens", params.model_dump())


def set_rotkey_request(params: SetRotkeyParams) -> DBRequest:
  return _request("set_rotkey", params.model_dump(exclude_none=True))


def list_snapshots_request(params: ListSessionSnapshotsParams) -> DBRequest:
  return _request("list_snapshots", params.model_dump())
