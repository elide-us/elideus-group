"""System role metadata registry bindings."""

from __future__ import annotations

from server.registry.types import DBRequest
from .model import (
  DeleteRoleParams,
  ModifyRoleMemberParams,
  RoleScopeParams,
  UpsertRoleParams,
)

__all__ = [
  "add_role_member_request",
  "delete_role_request",
  "get_role_members_request",
  "get_role_non_members_request",
  "list_roles_request",
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
