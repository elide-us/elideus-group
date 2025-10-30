"""System role metadata registry bindings."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest
from .model import (
  DeleteRoleParams,
  ModifyRoleMemberParams,
  RoleScopeParams,
  UpsertRoleParams,
)

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "add_role_member_request",
  "delete_role_request",
  "get_role_members_request",
  "get_role_non_members_request",
  "list_roles_request",
  "register",
  "remove_role_member_request",
  "upsert_role_request",
  "DeleteRoleParams",
  "ModifyRoleMemberParams",
  "RoleScopeParams",
  "UpsertRoleParams",
]


def list_roles_request() -> DBRequest:
  return DBRequest(op="db:system:roles:list:1", payload={})


def get_role_members_request(params: RoleScopeParams) -> DBRequest:
  return DBRequest(
    op="db:system:roles:get_role_members:1",
    payload=params.model_dump(),
  )


def get_role_non_members_request(params: RoleScopeParams) -> DBRequest:
  return DBRequest(
    op="db:system:roles:get_role_non_members:1",
    payload=params.model_dump(),
  )


def add_role_member_request(params: ModifyRoleMemberParams) -> DBRequest:
  return DBRequest(
    op="db:system:roles:add_role_member:1",
    payload=params.model_dump(),
  )


def remove_role_member_request(params: ModifyRoleMemberParams) -> DBRequest:
  return DBRequest(
    op="db:system:roles:remove_role_member:1",
    payload=params.model_dump(),
  )


def upsert_role_request(params: UpsertRoleParams) -> DBRequest:
  return DBRequest(
    op="db:system:roles:upsert_role:1",
    payload=params.model_dump(),
  )


def delete_role_request(params: DeleteRoleParams) -> DBRequest:
  return DBRequest(
    op="db:system:roles:delete_role:1",
    payload=params.model_dump(),
  )


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="list", version=1, implementation="list_roles")
  register_op(name="get_role_members", version=1)
  register_op(name="get_role_non_members", version=1)
  register_op(name="add_role_member", version=1)
  register_op(name="remove_role_member", version=1)
  register_op(name="upsert_role", version=1)
  register_op(name="delete_role", version=1)
