"""System public_vars query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from queryregistry.models import DBRequest, DBResponse

from . import mssql

__all__ = [
  "get_hostname_v1",
  "get_repo_v1",
  "get_version_v1",
]

_PublicVarDispatcher = Callable[[], Awaitable[DBResponse]]

_PROVIDER_DISPATCHERS: dict[str, dict[str, _PublicVarDispatcher]] = {
  "get_hostname": {
    "mssql": mssql.get_hostname,
  },
  "get_version": {
    "mssql": mssql.get_version,
  },
  "get_repo": {
    "mssql": mssql.get_repo,
  },
}


def _get_dispatcher(provider: str, operation: str) -> _PublicVarDispatcher:
  dispatchers = _PROVIDER_DISPATCHERS.get(operation)
  if dispatchers is None:
    raise KeyError(f"Unsupported public_vars operation '{operation}'")
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(
      f"Unsupported provider '{provider}' for system public_vars {operation}"
    )
  return dispatcher


async def get_hostname_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _get_dispatcher(provider, "get_hostname")
  result = await dispatcher()
  return DBResponse(op=request.op, payload=result.payload)


async def get_version_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _get_dispatcher(provider, "get_version")
  result = await dispatcher()
  return DBResponse(op=request.op, payload=result.payload)


async def get_repo_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _get_dispatcher(provider, "get_repo")
  result = await dispatcher()
  return DBResponse(op=request.op, payload=result.payload)
