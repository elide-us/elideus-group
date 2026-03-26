"""Identity roles query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import SetRolesParams, UserGuidParams

__all__ = [
  "add_role_member_v1",
  "get_roles_v1",
  "list_all_role_memberships_v1",
  "list_role_members_v1",
  "list_role_non_members_v1",
  "remove_role_member_v1",
  "set_roles_v1",
]

_ListMembersDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_ListAllMembersDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_ListNonMembersDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_AddMemberDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_RemoveMemberDispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]
_RolesDispatcher = Callable[[dict[str, Any]], Awaitable[DBResponse]]

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

_GET_ROLES_DISPATCHERS: dict[str, _RolesDispatcher] = {
  "mssql": mssql.get_roles_v1,
}

_SET_ROLES_DISPATCHERS: dict[str, _RolesDispatcher] = {
  "mssql": mssql.set_roles_v1,
}


def _select_dispatcher(provider: str, dispatchers: dict[str, Callable[..., Awaitable[DBResponse]]]):
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity roles registry")
  return dispatcher


async def list_role_members_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_MEMBERS_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def list_all_role_memberships_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_ALL_MEMBERS_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def list_role_non_members_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_NON_MEMBERS_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def add_role_member_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  result = await _select_dispatcher(provider, _ADD_MEMBER_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def remove_role_member_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  result = await _select_dispatcher(provider, _REMOVE_MEMBER_DISPATCHERS)(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def get_roles_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UserGuidParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_ROLES_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_roles_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetRolesParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _SET_ROLES_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
