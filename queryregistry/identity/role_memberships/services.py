"""Identity role memberships query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql

__all__ = [
  "add_role_member_v1",
  "list_all_role_memberships_v1",
  "list_role_members_v1",
  "list_role_non_members_v1",
  "remove_role_member_v1",
]

_ListMembersDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_ListAllMembersDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_ListNonMembersDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_AddMemberDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_RemoveMemberDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_MEMBERS_DISPATCHERS: dict[str, _ListMembersDispatcher] = {
  "mssql": mssql.list_role_members,
}

_LIST_ALL_MEMBERS_DISPATCHERS: dict[str, _ListAllMembersDispatcher] = {
  "mssql": mssql.list_all_role_memberships,
}

_LIST_NON_MEMBERS_DISPATCHERS: dict[str, _ListNonMembersDispatcher] = {
  "mssql": mssql.list_role_non_members,
}

_ADD_MEMBER_DISPATCHERS: dict[str, _AddMemberDispatcher] = {
  "mssql": mssql.add_role_member,
}

_REMOVE_MEMBER_DISPATCHERS: dict[str, _RemoveMemberDispatcher] = {
  "mssql": mssql.remove_role_member,
}


async def list_role_members_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _LIST_MEMBERS_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity role_memberships registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def list_all_role_memberships_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _LIST_ALL_MEMBERS_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity role_memberships registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def list_role_non_members_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _LIST_NON_MEMBERS_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity role_memberships registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def add_role_member_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _ADD_MEMBER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity role_memberships registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def remove_role_member_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _REMOVE_MEMBER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity role_memberships registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)
