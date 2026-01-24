"""Identity sessions query registry service dispatchers."""

from __future__ import annotations

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import RotkeyCallable, SecuritySnapshotCallable

__all__ = [
  "get_rotkey_v1",
  "read_sessions_v1",
]

_READ_DISPATCHERS: dict[str, SecuritySnapshotCallable] = {
  "mssql": mssql.get_security_snapshot_v1,
}

_ROTKEY_DISPATCHERS: dict[str, RotkeyCallable] = {
  "mssql": mssql.get_rotkey_v1,
}


async def get_rotkey_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _ROTKEY_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity sessions registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def read_sessions_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _READ_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity sessions registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)
