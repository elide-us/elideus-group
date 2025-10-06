"""Compatibility wrappers for account profile providers."""

from __future__ import annotations

from typing import Any

from server.registry.types import DBResponse
from server.registry.users.profile import mssql as _users_profile

__all__ = [
  "get_profile_v1",
  "set_display_v1",
  "set_optin_v1",
  "set_profile_image_v1",
  "set_roles_v1",
  "update_if_unedited_v1",
]

run_exec = _users_profile.run_exec
run_json_one = _users_profile.run_json_one


async def get_profile_v1(args: dict[str, Any]) -> DBResponse:
  return await _users_profile.get_profile_v1(args)


async def set_display_v1(args: dict[str, Any]) -> DBResponse:
  return await _users_profile.set_display_v1(args)


async def set_optin_v1(args: dict[str, Any]) -> DBResponse:
  return await _users_profile.set_optin_v1(args)


async def set_profile_image_v1(args: dict[str, Any]) -> DBResponse:
  return await _users_profile.set_profile_image_v1(args)


async def set_roles_v1(args: dict[str, Any]) -> DBResponse:
  return await _users_profile.set_roles_v1(args)


async def update_if_unedited_v1(args: dict[str, Any]) -> DBResponse:
  return await _users_profile.update_if_unedited_v1(args)
