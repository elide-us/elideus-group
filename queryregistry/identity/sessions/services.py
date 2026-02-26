"""Identity sessions query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
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
  "create_session_v1",
  "get_rotkey_v1",
  "list_snapshots_v1",
  "read_sessions_v1",
  "revoke_all_device_tokens_v1",
  "revoke_device_token_v1",
  "revoke_provider_tokens_v1",
  "set_rotkey_v1",
  "update_device_token_v1",
  "update_session_v1",
]

SessionOperationCallable = Callable[[dict[str, Any]], Awaitable[DBResponse]]

_READ_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.get_security_snapshot_v1,
}

_ROTKEY_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.get_rotkey_v1,
}

_CREATE_SESSION_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.create_session_v1,
}

_UPDATE_SESSION_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.update_session_v1,
}

_UPDATE_DEVICE_TOKEN_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.update_device_token_v1,
}

_REVOKE_DEVICE_TOKEN_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.revoke_device_token_v1,
}

_REVOKE_ALL_DEVICE_TOKENS_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.revoke_all_device_tokens_v1,
}

_REVOKE_PROVIDER_TOKENS_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.revoke_provider_tokens_v1,
}

_SET_ROTKEY_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.set_rotkey_v1,
}

_LIST_SNAPSHOTS_DISPATCHERS: dict[str, SessionOperationCallable] = {
  "mssql": mssql.list_snapshots_v1,
}


def _resolve_dispatcher(
  dispatchers: dict[str, SessionOperationCallable],
  *,
  provider: str,
) -> SessionOperationCallable:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity sessions registry")
  return dispatcher


async def create_session_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_CREATE_SESSION_DISPATCHERS, provider=provider)
  params = CreateSessionParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump(exclude_none=True))
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def update_session_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_UPDATE_SESSION_DISPATCHERS, provider=provider)
  params = UpdateSessionParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_device_token_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_UPDATE_DEVICE_TOKEN_DISPATCHERS, provider=provider)
  params = UpdateDeviceTokenParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def revoke_device_token_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_REVOKE_DEVICE_TOKEN_DISPATCHERS, provider=provider)
  params = RevokeDeviceTokenParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def revoke_all_device_tokens_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_REVOKE_ALL_DEVICE_TOKENS_DISPATCHERS, provider=provider)
  params = RevokeAllDeviceTokensParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def revoke_provider_tokens_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_REVOKE_PROVIDER_TOKENS_DISPATCHERS, provider=provider)
  params = RevokeProviderTokensParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_rotkey_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_SET_ROTKEY_DISPATCHERS, provider=provider)
  params = SetRotkeyParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump(exclude_none=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_snapshots_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_LIST_SNAPSHOTS_DISPATCHERS, provider=provider)
  params = ListSessionSnapshotsParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_rotkey_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_ROTKEY_DISPATCHERS, provider=provider)
  params = RotkeyLookupParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump(exclude_none=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def read_sessions_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _resolve_dispatcher(_READ_DISPATCHERS, provider=provider)
  params = GuidParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
