"""System roles query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql

__all__ = [
  "delete_role_v1",
  "list_roles_v1",
  "upsert_role_v1",
]

_ListRolesDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_UpsertRoleDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_DeleteRoleDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_DISPATCHERS: dict[str, _ListRolesDispatcher] = {
  "mssql": mssql.list_roles,
}

_UPSERT_DISPATCHERS: dict[str, _UpsertRoleDispatcher] = {
  "mssql": mssql.upsert_role,
}

_DELETE_DISPATCHERS: dict[str, _DeleteRoleDispatcher] = {
  "mssql": mssql.delete_role,
}


async def list_roles_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _LIST_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system roles registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def upsert_role_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _UPSERT_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system roles registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def delete_role_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _DELETE_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system roles registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)
