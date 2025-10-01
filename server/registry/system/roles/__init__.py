"""System role metadata registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from . import mssql  # noqa: F401

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "add_role_member_request",
  "delete_role_request",
  "get_role_members_request",
  "get_role_non_members_request",
  "list_roles_request",
  "register",
  "remove_role_member_request",
  "upsert_role_request",
]

_DEF_PROVIDER = "system.roles"


def list_roles_request() -> DBRequest:
  return DBRequest(op="db:system:roles:list:1", params={})


def get_role_members_request(role: str) -> DBRequest:
  return DBRequest(op="db:system:roles:get_role_members:1", params={"role": role})


def get_role_non_members_request(role: str) -> DBRequest:
  return DBRequest(op="db:system:roles:get_role_non_members:1", params={"role": role})


def add_role_member_request(role: str, user_guid: str) -> DBRequest:
  return DBRequest(op="db:system:roles:add_role_member:1", params={
    "role": role,
    "user_guid": user_guid,
  })


def remove_role_member_request(role: str, user_guid: str) -> DBRequest:
  return DBRequest(op="db:system:roles:remove_role_member:1", params={
    "role": role,
    "user_guid": user_guid,
  })


def upsert_role_request(name: str, mask: int, display: str | None) -> DBRequest:
  return DBRequest(op="db:system:roles:upsert_role:1", params={
    "name": name,
    "mask": mask,
    "display": display,
  })


def delete_role_request(name: str) -> DBRequest:
  return DBRequest(op="db:system:roles:delete_role:1", params={"name": name})


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "list",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.list",
  )
  router.add_function(
    "get_role_members",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.get_role_members",
  )
  router.add_function(
    "get_role_non_members",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.get_role_non_members",
  )
  router.add_function(
    "add_role_member",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.add_role_member",
  )
  router.add_function(
    "remove_role_member",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.remove_role_member",
  )
  router.add_function(
    "upsert_role",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.upsert_role",
  )
  router.add_function(
    "delete_role",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.delete_role",
  )
