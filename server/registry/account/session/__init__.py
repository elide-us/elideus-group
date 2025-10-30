"""Account session registry helpers."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest
from .model import (
  CreateSessionParams,
  GuidParams,
  ListSessionSnapshotsParams,
  RevokeAllDeviceTokensParams,
  RevokeDeviceTokenParams,
  RevokeProviderTokensParams,
  SetRotkeyParams,
  UpdateDeviceTokenParams,
  UpdateSessionParams,
)

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "create_session_request",
  "get_rotkey_request",
  "register",
  "revoke_all_device_tokens_request",
  "revoke_device_token_request",
  "revoke_provider_tokens_request",
  "get_security_snapshot_request",
  "set_rotkey_request",
  "list_session_snapshots_request",
  "update_device_token_request",
  "update_session_request",
  "CreateSessionParams",
  "GuidParams",
  "ListSessionSnapshotsParams",
  "RevokeAllDeviceTokensParams",
  "RevokeDeviceTokenParams",
  "RevokeProviderTokensParams",
  "SetRotkeyParams",
  "UpdateDeviceTokenParams",
  "UpdateSessionParams",
]


def _request(name: str, params: dict[str, object]) -> DBRequest:
  return DBRequest(op=f"db:account:session:{name}:1", payload=params)


def list_session_snapshots_request(params: ListSessionSnapshotsParams) -> DBRequest:
  return _request("list_snapshots", params.model_dump())


def get_security_snapshot_request(params: GuidParams) -> DBRequest:
  return _request("get_security_snapshot", params.model_dump())


def create_session_request(params: CreateSessionParams) -> DBRequest:
  payload = params.model_dump(exclude_none=True)
  return _request("create_session", payload)


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


def get_rotkey_request(params: GuidParams) -> DBRequest:
  return _request("get_rotkey", params.model_dump())


def set_rotkey_request(params: SetRotkeyParams) -> DBRequest:
  return _request("set_rotkey", params.model_dump())


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="create_session", version=1)
  register_op(name="update_session", version=1)
  register_op(name="update_device_token", version=1)
  register_op(name="revoke_device_token", version=1)
  register_op(name="revoke_all_device_tokens", version=1)
  register_op(name="revoke_provider_tokens", version=1)
  register_op(name="get_rotkey", version=1)
  register_op(name="set_rotkey", version=1)
  register_op(name="list_snapshots", version=1)
  register_op(name="get_security_snapshot", version=1)
