"""System role metadata registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

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
_PROVIDER_MODULE = "server.registry.system.roles.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "list": "list_roles_v1",
  "get_role_members": "get_role_members_v1",
  "get_role_non_members": "get_role_non_members_v1",
  "add_role_member": "add_role_member_v1",
  "remove_role_member": "remove_role_member_v1",
  "upsert_role": "upsert_role_v1",
  "delete_role": "delete_role_v1",
}


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
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
