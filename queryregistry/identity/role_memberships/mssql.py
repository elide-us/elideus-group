"""MSSQL implementations for identity role memberships query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from server.registry.system.roles.mssql import (
  add_role_member_v1,
  get_role_members_v1,
  get_role_non_members_v1,
  remove_role_member_v1,
)

from queryregistry.models import DBResponse

__all__ = [
  "add_role_member",
  "list_role_members",
  "list_role_non_members",
  "remove_role_member",
]


async def list_role_members(args: Mapping[str, Any]) -> DBResponse:
  response = await get_role_members_v1(dict(args))
  return DBResponse(payload=response.payload)


async def list_role_non_members(args: Mapping[str, Any]) -> DBResponse:
  response = await get_role_non_members_v1(dict(args))
  return DBResponse(payload=response.payload)


async def add_role_member(args: Mapping[str, Any]) -> DBResponse:
  response = await add_role_member_v1(dict(args))
  return DBResponse(payload={"rowcount": response.rowcount})


async def remove_role_member(args: Mapping[str, Any]) -> DBResponse:
  response = await remove_role_member_v1(dict(args))
  return DBResponse(payload={"rowcount": response.rowcount})
